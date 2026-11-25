#!/usr/bin/env python3
"""案件云 Open API 调用脚本

用法:
    python3 api.py GET /cases
    python3 api.py GET "/cases?keyword=张三&g_status=1"
    python3 api.py POST /calendar '{"title":"开庭","htime":"2026-04-30 14:00","endtime":"2026-04-30 15:00"}'
    python3 api.py PATCH /cases/ABC123 '{"stage_text":"已开庭"}'
    python3 api.py PUT /calendar/abc123 '{"title":"新标题"}'
    python3 api.py DELETE /calendar/abc123
    python3 api.py UPLOAD /cases/ABC123/files /path/to/file.pdf
    python3 api.py UPLOAD /cases/ABC123/files /path/to/file.pdf '{"folder_id":0}'

自动从同目录的 .env 文件加载 API_BASE_URL 和 PAT_TOKEN。
"""

import sys
import os
import json
import re
import io

try:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
    from urllib.parse import quote, urlparse, quote_plus
except ImportError:
    from urllib2 import Request, urlopen, HTTPError, URLError

import mimetypes
import uuid


def load_env():
    """从 skill 目录加载 .env（先找脚本同级，再找上级 skill 根目录）"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, '.env'),
        os.path.join(script_dir, '..', '.env'),
    ]
    env_path = None
    for p in candidates:
        if os.path.exists(p):
            env_path = p
            break

    env = {}
    if not env_path:
        print(json.dumps({
            'code': -1,
            'msg': '.env 文件不存在',
            'hint': '请复制 .env.example 为 .env 并填入 PAT_TOKEN'
        }, ensure_ascii=False))
        sys.exit(1)

    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                env[key.strip()] = value.strip()

    base_url = env.get('API_BASE_URL', '').rstrip('/')
    token = env.get('PAT_TOKEN', '')

    if not base_url:
        print(json.dumps({'code': -1, 'msg': 'API_BASE_URL 未配置'}, ensure_ascii=False))
        sys.exit(1)

    if not token or 'xxx' in token:
        print(json.dumps({
            'code': -1,
            'msg': 'PAT_TOKEN 未配置或仍为占位值',
            'hint': '请在案件云 OA「个人设置 > AI管理」中生成 PAT，填入 .env'
        }, ensure_ascii=False))
        sys.exit(1)

    return base_url, token


def make_request(method, base_url, token, path, body=None):
    """发送 HTTP 请求并返回格式化的响应"""
    # 确保 path 以 / 开头
    if not path.startswith('/'):
        path = '/' + path

    # 对 URL 中的非 ASCII 字符进行编码
    if '?' in path:
        path_base, query = path.split('?', 1)
        pairs = []
        for part in query.split('&'):
            if '=' in part:
                k, v = part.split('=', 1)
                pairs.append('{}={}'.format(quote_plus(k), quote_plus(v, safe='')))
            else:
                pairs.append(quote_plus(part))
        path = path_base + '?' + '&'.join(pairs)

    url = base_url + path

    headers = {
        'Authorization': 'Bearer {}'.format(token),
        'Accept': 'application/json',
    }

    data = None
    if body is not None:
        headers['Content-Type'] = 'application/json; charset=utf-8'
        data = json.dumps(body, ensure_ascii=False).encode('utf-8')

    req = Request(url, data=data, headers=headers)
    req.method = method.upper()

    try:
        response = urlopen(req, timeout=30)
        resp_bytes = response.read()
        encoding = response.headers.get_content_charset() or 'utf-8'
        resp_text = resp_bytes.decode(encoding)

        try:
            resp_json = json.loads(resp_text)
        except (json.JSONDecodeError, ValueError):
            return {'code': -1, 'msg': '响应非 JSON', 'raw': resp_text[:500]}

        return resp_json

    except HTTPError as e:
        body_text = ''
        try:
            body_text = e.read().decode('utf-8', errors='replace')[:500]
        except Exception:
            pass

        if e.code == 401:
            return {
                'code': 2,
                'msg': 'Token 无效或已过期，请重新生成 PAT',
                'http_status': e.code
            }
        elif e.code == 403:
            # 优先透传服务端返回的具体 code/msg（如非拥有者拦截、无有效订阅等），回退默认提示
            try:
                err_json = json.loads(body_text) if body_text else {}
            except (json.JSONDecodeError, ValueError):
                err_json = {}
            err_code = err_json.get('code', 3)
            try:
                err_code = int(err_code)
            except (TypeError, ValueError):
                err_code = 3
            return {
                'code': err_code,
                'msg': err_json.get('msg') or '权限不足，请检查 PAT 的 scope 设置',
                'http_status': e.code
            }
        elif e.code == 404:
            return {
                'code': -1,
                'msg': '接口不存在: {} {}'.format(method, path),
                'http_status': e.code
            }
        else:
            return {
                'code': -1,
                'msg': 'HTTP {} 错误'.format(e.code),
                'http_status': e.code,
                'detail': body_text
            }

    except URLError as e:
        return {
            'code': -1,
            'msg': '网络错误: {}'.format(str(e.reason)),
            'hint': '请检查网络连接和 API_BASE_URL 是否正确'
        }

    except Exception as e:
        return {
            'code': -1,
            'msg': '请求异常: {}'.format(str(e))
        }


def make_upload_request(method, base_url, token, path, file_path, extra_fields=None):
    """OSS 直传两步流上传文件：
    ① POST {path}/policy 签发上传凭证（服务端校验：访问控制/文件名/大小分层/限额）
    ② multipart POST 到 OSS host 直传文件（字节不过业务服务器，nginx/PHP 大小限制不适用），
       OSS 把回调落库结果透传回来（{code, msg, data}）
    """
    if not path.startswith('/'):
        path = '/'

    if not os.path.exists(file_path):
        return {'code': -1, 'msg': '文件不存在: {}'.format(file_path)}

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    # 全局上限提示（基础版 10M / 付费版 100M 由服务端 policy 判定，本地只挡 100M 硬顶）
    if file_size > 100 * 1024 * 1024:
        return {'code': -1, 'msg': '文件大小超过100MB上限（付费版最大 100MB、基础版 10MB）'}

    # ① 签发凭证（extra_fields 里的 folder_id/record_id 一并带入）
    policy_body = {'file_name': file_name, 'size': file_size}
    for k in ('folder_id', 'record_id'):
        if extra_fields and k in extra_fields:
            policy_body[k] = extra_fields[k]

    policy_req = Request(
        base_url + path.rstrip('/') + '/policy',
        data=json.dumps(policy_body).encode('utf-8'),
        headers={'Authorization': 'Bearer {}'.format(token), 'Content-Type': 'application/json'},
    )
    policy_req.method = 'POST'

    try:
        resp = urlopen(policy_req, timeout=30)
        policy = json.loads(resp.read().decode('utf-8'))
    except HTTPError as e:
        try:
            err = json.loads(e.read().decode('utf-8'))
            return {'code': err.get('code', -1), 'msg': err.get('msg', '凭证签发失败'), 'http_status': e.code}
        except Exception:
            return {'code': -1, 'msg': '凭证签发失败: HTTP {}'.format(e.code), 'http_status': e.code}
    except Exception as e:
        return {'code': -1, 'msg': '凭证签发请求异常: {}'.format(str(e))}

    if policy.get('code') != 0:
        return policy

    cfg = policy.get('data') or {}
    for field in ('host', 'key', 'policy', 'signature', 'accessid', 'callback'):
        if not cfg.get(field):
            return {'code': -1, 'msg': '上传凭证字段缺失: {}'.format(field)}

    # ② 直传 OSS（PostObject 协议：表单域顺序无关但 file 必须最后；
    #    callback-var 的每个变量按协议拆成独立 x:xxx 表单域）
    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = 'application/octet-stream'

    boundary = uuid.uuid4().hex
    lines = []

    def add_field(name, value):
        lines.append('--{}'.format(boundary))
        lines.append('Content-Disposition: form-data; name="{}"'.format(name))
        lines.append('')
        lines.append(str(value))

    add_field('key', cfg['key'])
    add_field('policy', cfg['policy'])
    add_field('OSSAccessKeyId', cfg['accessid'])
    add_field('success_action_status', '200')
    add_field('signature', cfg['signature'])
    add_field('callback', cfg['callback'])
    for var_name, var_value in (cfg.get('callback-var') or {}).items():
        add_field(var_name, var_value)

    # 文件域必须在最后
    lines.append('--{}'.format(boundary))
    lines.append('Content-Disposition: form-data; name="file"; filename="{}"'.format(file_name))
    lines.append('Content-Type: {}'.format(content_type))
    lines.append('')
    lines.append('')

    body_prefix = '\r\n'.join(lines).encode('utf-8')
    body_suffix = '\r\n--{}--\r\n'.format(boundary).encode('utf-8')

    with open(file_path, 'rb') as f:
        body = body_prefix + f.read() + body_suffix

    oss_req = Request(cfg['host'], data=body, headers={
        'Content-Type': 'multipart/form-data; boundary={}'.format(boundary),
    })
    oss_req.method = 'POST'

    try:
        response = urlopen(oss_req, timeout=300)
        resp_text = response.read().decode('utf-8', errors='replace')
        try:
            # OSS 透传回调端点的响应体（{code,msg,data}，code=0 即落库成功）
            return json.loads(resp_text)
        except (json.JSONDecodeError, ValueError):
            return {'code': -1, 'msg': 'OSS 响应非 JSON', 'raw': resp_text[:500]}

    except HTTPError as e:
        oss_err = ''
        try:
            oss_err = e.read().decode('utf-8', errors='replace')[:500]
        except Exception:
            pass
        # OSS 层错误为 XML（如 EntityTooLarge：绕过声明 size 直传超限文件）
        import re as _re
        code_m = _re.search(r'<Code>([^<]+)</Code>', oss_err)
        oss_code = code_m.group(1) if code_m else 'HTTP {}'.format(e.code)
        friendly = {
            'EntityTooLarge': '文件大小超过限制（基础版 10MB / 付费版 100MB），请到 OA 网页端上传或压缩文件',
            'AccessDenied': 'OSS 拒绝访问（凭证可能已过期，请重试）',
            'CallbackFailed': '文件已上传但服务器回调失败，请到 OA 核对是否落库后再决定是否重试',
        }.get(oss_code)
        return {
            'code': -1,
            'msg': friendly or 'OSS 上传失败: {}'.format(oss_code),
            'oss_code': oss_code,
            'detail': oss_err,
        }

    except URLError as e:
        return {'code': -1, 'msg': '网络错误: {}'.format(str(e.reason))}

    except Exception as e:
        return {'code': -1, 'msg': '请求异常: {}'.format(str(e))}


def _ensure_stdout_utf8():
    """强制 stdout/stderr 使用 UTF-8 编码，避免中文乱码"""
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def main():
    _ensure_stdout_utf8()

    if len(sys.argv) < 3:
        print('用法: python3 api.py <METHOD> <PATH> [JSON_BODY]')
        print('      python3 api.py UPLOAD <PATH> <FILE_PATH> [JSON_FIELDS]')
        print('示例: python3 api.py GET /cases')
        print('      python3 api.py POST /calendar \'{"title":"开庭"}\'')
        print('      python3 api.py PATCH /records/abc123 \'{"hstatus":1}\'')
        print('      python3 api.py UPLOAD /cases/ABC123/files /path/to/file.pdf')
        sys.exit(1)

    method = sys.argv[1].upper()
    path = sys.argv[2]

    if method == 'UPLOAD':
        if len(sys.argv) < 4:
            print('用法: python3 api.py UPLOAD <PATH> <FILE_PATH> [JSON_FIELDS]')
            sys.exit(1)

        file_path = sys.argv[3]
        extra_fields = None
        if len(sys.argv) > 4:
            try:
                extra_fields = json.loads(sys.argv[4])
            except json.JSONDecodeError as e:
                print(json.dumps({
                    'code': -1,
                    'msg': 'JSON 解析失败: {}'.format(str(e)),
                    'input': sys.argv[4][:200]
                }, ensure_ascii=False))
                sys.exit(1)

        base_url, token = load_env()
        result = make_upload_request('UPLOAD', base_url, token, path, file_path, extra_fields)

    elif method not in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'):
        print(json.dumps({
            'code': -1,
            'msg': '不支持的 HTTP 方法: {}'.format(method),
            'supported': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'UPLOAD']
        }, ensure_ascii=False))
        sys.exit(1)

    else:
        body = None
        if len(sys.argv) > 3:
            try:
                body = json.loads(sys.argv[3])
            except json.JSONDecodeError as e:
                print(json.dumps({
                    'code': -1,
                    'msg': 'JSON 解析失败: {}'.format(str(e)),
                    'input': sys.argv[3][:200]
                }, ensure_ascii=False))
                sys.exit(1)

        base_url, token = load_env()
        result = make_request(method, base_url, token, path, body)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
