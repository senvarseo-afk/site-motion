#!/usr/bin/env python3
"""site-motion 靜態稽核：掃專案原始碼，列出動態現況與風險。只讀檔，不改任何東西。
用法：python3 motion_audit.py <專案目錄> [--json]
結果是線索不是判決：regex 掃描會有誤判，實際手感要到手機寬度點過才算數。"""
import json, os, re, sys

SKIP = {'node_modules', 'dist', 'build', '.git', '.astro', '.next', '.nuxt', '.output', 'vendor', 'coverage'}
EXT = {'.astro', '.css', '.scss', '.js', '.mjs', '.ts', '.tsx', '.jsx', '.vue', '.svelte', '.html', '.php'}
LIBS = ['gsap', 'framer-motion', 'motion', 'lottie-web', '@lottiefiles/dotlottie-web', 'aos', 'swiper',
        'animejs', 'three', '@barba/core', 'locomotive-scroll', 'lenis', 'swup']
LAYOUT = r'(?:width|height|top|left|right|bottom|margin[a-z-]*|padding[a-z-]*)'


def walk(root):
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith('.')]
        for f in files:
            if os.path.splitext(f)[1] in EXT:
                p = os.path.join(base, f)
                try:
                    if os.path.getsize(p) > 1500000:
                        continue
                    yield os.path.relpath(p, root), open(p, encoding='utf-8', errors='ignore').read()
                except OSError:
                    pass


def hits(files, pattern, flags=0, limit=8):
    rx = re.compile(pattern, flags)
    found = []
    for path, text in files:
        for m in rx.finditer(text):
            found.append('%s:%d' % (path, text.count('\n', 0, m.start()) + 1))
    return {'count': len(found), 'where': found[:limit]}


def detect(root):
    pkg = {}
    try:
        pkg = json.load(open(os.path.join(root, 'package.json'), encoding='utf-8'))
    except (OSError, ValueError):
        pass
    deps = dict(pkg.get('dependencies', {}), **pkg.get('devDependencies', {}))
    fw = 'unknown'
    for key, name in (('astro', 'Astro'), ('next', 'Next.js'), ('nuxt', 'Nuxt'), ('@sveltejs/kit', 'SvelteKit'),
                      ('react', 'React'), ('vue', 'Vue')):
        if key in deps:
            fw = '%s %s' % (name, deps[key])
            break
    if fw == 'unknown' and os.path.exists(os.path.join(root, 'wp-config.php')):
        fw = 'WordPress'
    return fw, deps


def audit(root):
    fw, deps = detect(root)
    files = list(walk(root))
    styles = [(p, t) for p, t in files if p.endswith(('.css', '.scss', '.astro', '.vue', '.svelte'))]
    astro = fw.startswith('Astro')
    keyframes = []
    for path, text in styles:
        for m in re.finditer(r'@keyframes\s+([\w-]+)\s*\{((?:[^{}]*\{[^{}]*\})*)', text):
            if re.search(r'[{;\s]' + LAYOUT + r'\s*:', m.group(2)):
                keyframes.append('%s:%d (%s)' % (path, text.count('\n', 0, m.start()) + 1, m.group(1)))
    r = {
        'project': os.path.abspath(root), 'framework': fw, 'files_scanned': len(files),
        'libraries': {k: deps[k] for k in LIBS if k in deps},
        'soft_nav': {
            'client_router': hits(files, r'<(?:ClientRouter|ViewTransitions)\b'),
            'cross_document_vt': hits(styles, r'@view-transition'),
            'start_view_transition': hits(files, r'startViewTransition'),
            'transition_name': hits(files, r'transition:name|view-transition-name'),
            'transition_persist': hits(files, r'transition:persist'),
            'optional_transition_name': hits(files, r'transition:name=\{\s*[a-zA-Z_]\w*\s*\}'),
            'prefetch': hits(files, r'\bprefetch\b|speculationrules'),
        },
        'motion': {
            'reduced_motion': hits(styles, r'prefers-reduced-motion'),
            'css_transition': hits(styles, r'\btransition\s*:'),
            'css_animation': hits(styles, r'\banimation\s*:'),
            'transition_all': hits(styles, r'transition\s*:\s*all\b'),
            'layout_transition': hits(styles, r'transition\s*:[^;}]*\b' + LAYOUT + r'\b'),
            'layout_keyframes': {'count': len(keyframes), 'where': keyframes[:8]},
            'has_active_state': hits(styles, r':active\b'),
        },
        'script_risks': {
            'page_load_hook': hits(files, r'astro:page-load'),
            'domcontentloaded': hits(files, r'DOMContentLoaded'),
            'location_reload': hits(files, r'location\.reload\('),
            'set_interval': hits(files, r'setInterval\('),
            'intersection_observer': hits(files, r'IntersectionObserver'),
            'hidden_until_reveal': hits(styles, r'opacity\s*:\s*0\b'),
        },
        'analytics_ads': {
            'gtag_config': hits(files, r"gtag\(\s*['\"]config['\"]"),
            'manual_page_view': hits(files, r"['\"]page_view['\"]"),
            'send_page_view_false': hits(files, r'send_page_view'),
            'adsense': hits(files, r'adsbygoogle'),
            'ad_slot_component': hits(files, r'data-ad-slot|class=.?["\'`]ad\b'),
        },
    }
    notes, sn, mo, sc, an = [], r['soft_nav'], r['motion'], r['script_risks'], r['analytics_ads']
    router = sn['client_router']['count'] > 0
    framework_router = fw.split(' ')[0] in ('Next.js', 'Nuxt', 'SvelteKit', 'React', 'Vue')
    soft = router or framework_router
    n = notes.append
    if r['files_scanned'] < 5:
        n('掃到的檔案很少，專案可能只是空殼，以下結果參考價值低。')
    if framework_router and not router:
        n('框架路由可能已是軟導覽（React、Vue 要看專案是否用路由），下面的分析與廣告提醒要逐筆確認。')
    if not soft and not sn['cross_document_vt']['count'] and not sn['start_view_transition']['count']:
        n('切頁是整頁重載：沒有 ClientRouter 或 View Transitions。「按了就跳頁」的感覺通常從這裡來。')
    if not sn['prefetch']['count']:
        if router:
            n('ClientRouter 預設 prefetch 策略是 hover，手機上幾乎沒作用，列表考慮用 tap 或 viewport。')
        elif not framework_router:
            n('沒有 prefetch：點下去要等網路。')
    if soft and an['ad_slot_component']['count'] + an['adsense']['count']:
        n('高風險：同文件軟導覽加廣告沒有官方專文，開廣告前要實測，或改跨文件 @view-transition。')
    if router and not sn['transition_persist']['count']:
        n('有軟導覽但沒有 transition:persist：頁首、底導會跟著重繪。')
    if sn['optional_transition_name']['count']:
        n('高風險：transition:name 用變數傳值，沒給值時 Astro 會自動命名，列表頁 HTML 可能暴增，逐筆確認。')
    if not mo['reduced_motion']['count']:
        n('高風險：沒有 prefers-reduced-motion，動效要先補這一層。')
    if not mo['has_active_state']['count']:
        n('沒有 :active 壓感：手機上按下去沒有回饋。')
    if mo['transition_all']['count']:
        n('有 transition: all，容易動到版面屬性，建議列出具體屬性。')
    if mo['layout_transition']['count'] or mo['layout_keyframes']['count']:
        n('有用版面屬性做動畫的線索（width/height/top 等），可能造成 CLS 或掉幀，逐筆確認；脫離文件流的小指示條影響小，grid-template-rows 展開不算。')
    if router and sc['domcontentloaded']['count']:
        n('開了軟導覽仍有 DOMContentLoaded，切頁後不會重跑；若旁邊已有 astro:page-load 綁定通常是保護寫法，逐筆確認。'
          if sc['page_load_hook']['count'] else '高風險：開了軟導覽仍有 DOMContentLoaded，切頁後這些綁定不會重跑。')
    if soft and sc['location_reload']['count']:
        n('開了軟導覽仍有 location.reload()，使用者會看到整頁重載，評估改用 navigate()。')
    if sc['intersection_observer']['count'] and sc['hidden_until_reveal']['count']:
        n('有捲動顯示的線索：確認內容不會卡在 opacity: 0，資料區塊不要做。')
    if soft and an['gtag_config']['count'] and not an['manual_page_view']['count']:
        n('高風險：GA4 只在首次載入 config。軟導覽的 page_view 要靠 Enhanced measurement 的 history 事件，且自訂參數不會更新。')
    if soft and an['manual_page_view']['count'] and not an['send_page_view_false']['count']:
        n('高風險：手動送 page_view，要確認 GA4 的 Enhanced measurement history 事件沒有同時開，否則重複計算。')
    return r, notes


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args or not os.path.isdir(args[0]):
        sys.exit('用法：python3 motion_audit.py <專案目錄> [--json]')
    r, notes = audit(args[0])
    if not r['files_scanned']:
        sys.exit('這個目錄沒有網站原始碼可掃（只掃 .astro .css .js .ts .html .php 等），請指定專案根目錄。')
    if '--json' in sys.argv:
        print(json.dumps(dict(r, notes=notes), ensure_ascii=False, indent=1))
        return
    print('# 動態稽核：%s\n\n- 框架：%s\n- 掃描檔案：%d\n- 動畫函式庫：%s\n' % (
        r['project'], r['framework'], r['files_scanned'],
        '、'.join('%s %s' % kv for kv in r['libraries'].items()) or '無'))
    print('## 需要注意\n')
    for x in notes or ['靜態掃描沒有發現明顯問題。']:
        print('- ' + x)
    for sec in ('soft_nav', 'motion', 'script_risks', 'analytics_ads'):
        print('\n## %s\n' % sec)
        for k, v in r[sec].items():
            print('- %s：%d%s' % (k, v['count'], '（' + '、'.join(v['where'][:3]) + '）' if v['count'] else ''))


if __name__ == '__main__':
    main()
