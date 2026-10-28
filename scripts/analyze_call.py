import os, sys, json, html, urllib.request
from pathlib import Path

source = Path(sys.argv[1])
record = json.loads(source.read_text(encoding='utf-8'))
segments = record.get('segments', [])
transcript = '\n'.join(f"[{s['start']:.1f}s–{s['end']:.1f}s] {s['text']}" for s in segments)
result = {'summary':'Chưa có phân tích','customer_issue':'Chưa xác định','resolution':'Chưa xác định','strengths':[],'improvements':[],'score':None,'score_reason':'Chưa đủ dữ liệu','evidence':[],'speaker_note':'Chưa phân biệt người nói bằng âm học'}
error = ''
key = os.getenv('DEEPSEEK_API_KEY', '')
if key and transcript:
    system = ('Bạn là chuyên viên đánh giá chất lượng chăm sóc khách hàng Việt Nam. '
              'Phân tích bản chép lời, trả về DUY NHẤT một JSON object có các khóa: '
              'summary, customer_issue, resolution, strengths (mảng chuỗi), improvements (mảng chuỗi), '
              'score (số 0-100 hoặc null), score_reason, evidence (mảng object gồm time, quote, reason), speaker_note. '
              'Chấm điểm theo: chào hỏi 10, lắng nghe 15, xác định vấn đề 20, rõ ràng 15, xử lý 25, kết thúc 15. '
              'Nếu không đủ bằng chứng để chấm chính xác, score=null. '
              'Không bịa lời nói, không xác nhận danh tính người nói từ văn bản; có thể suy luận vai trò nhưng phải ghi rõ mức độ không chắc chắn. '
              'Mọi nhận xét quan trọng phải có trích dẫn minh chứng và thời điểm. Không suy đoán cảm xúc từ âm thanh.')
    payload = {'model':'deepseek-chat', 'messages':[{'role':'system','content':system},{'role':'user','content':transcript[:90000]}], 'response_format':{'type':'json_object'},'temperature':0.1}
    try:
        req = urllib.request.Request('https://api.deepseek.com/chat/completions', data=json.dumps(payload).encode('utf-8'), headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=180) as response:
            result = json.loads(json.load(response)['choices'][0]['message']['content'])
    except Exception as ex:
        error = f'{type(ex).__name__}: {ex}'
else:
    error = 'Chưa cấu hình DEEPSEEK_API_KEY hoặc transcript rỗng'
result['error'] = error or None
out = Path('output'); out.mkdir(exist_ok=True)
(out/'call_analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2), encoding='utf-8')
esc = lambda v: html.escape(str(v if v is not None else 'Chưa đủ dữ liệu'))
def li(values): return '<ul>'+''.join('<li>'+esc(x)+'</li>' for x in (values or []))+'</ul>'
rows = ''.join('<tr><td>'+esc(x.get('time'))+'</td><td>'+esc(x.get('quote'))+'</td><td>'+esc(x.get('reason'))+'</td></tr>' for x in result.get('evidence',[]) if isinstance(x,dict))
lines = ''.join('<p><strong>'+esc(f"{s['start']:.1f}s")+'</strong> '+esc(s['text'])+'</p>' for s in segments)
page = '''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Báo cáo cuộc gọi</title><style>body{font:16px/1.6 Arial;background:#f3f6fb;color:#183047}main{max-width:950px;margin:25px auto;padding:15px}section{background:white;padding:22px;border-radius:12px;margin:16px 0;box-shadow:0 1px 10px #0001}h1,h2{color:#07609c}table{border-collapse:collapse;width:100%}td,th{padding:9px;border-bottom:1px solid #ddd;text-align:left}strong{color:#0684a4}</style></head><body><main><h1>BÁO CÁO ĐÁNH GIÁ CUỘC GỌI</h1><section><h2>Tổng quan</h2><p>'''+esc(result.get('summary'))+'''</p><p><b>Vấn đề:</b> '''+esc(result.get('customer_issue'))+'''</p><p><b>Hướng giải quyết:</b> '''+esc(result.get('resolution'))+'''</p><p><b>Điểm:</b> '''+esc(result.get('score'))+''' / 100</p><p>'''+esc(result.get('score_reason'))+'''</p></section><section><h2>Điểm mạnh</h2>'''+li(result.get('strengths'))+'''<h2>Cần cải thiện</h2>'''+li(result.get('improvements'))+'''</section><section><h2>Bằng chứng</h2><table><tr><th>Thời điểm</th><th>Lời nói</th><th>Nhận xét</th></tr>'''+rows+'''</table></section><section><h2>Bản chép lời</h2>'''+lines+'''</section><section><h2>Giới hạn</h2><p>'''+esc(result.get('speaker_note'))+'''</p><p>Hệ thống chưa tích hợp diarization bằng âm học. Bản chép lời có thể sai; kết quả AI cần được đối chiếu bản ghi trước khi đánh giá chính thức.</p><p>'''+esc(error)+'''</p></section></main></body></html>'''
(out/'call_report.html').write_text(page,encoding='utf-8')
print('Report generated: output/call_report.html')
