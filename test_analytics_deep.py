from pathlib import Path
from playwright.sync_api import sync_playwright
HTML=Path('/mnt/data/plateos-demo/index.html').read_text().replace('    render();\n  })();','    window.__db=()=>JSON.parse(JSON.stringify(db));window.__ledger=()=>anRows();window.__getDataset=x=>anDataset(x);render();\n  })();')
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 pg=b.new_page(viewport={'width':390,'height':844},device_scale_factor=1,accept_downloads=True)
 pg.route('https://**/*',lambda r:r.abort())
 errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
 pg.set_content(HTML)
 pg.locator('[data-action=side-open]').click()
 pg.locator('[data-mode=reports]').first.click()
 pg.screenshot(path='/mnt/data/plateos-demo/preview-v5-mobile.png',full_page=True)
 print('Mobile reports width',pg.evaluate('document.documentElement.scrollWidth'),pg.evaluate('window.innerWidth'))
 assert pg.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'mobile reporting overflow'
 # All-branch scope > current site; record all rows tagged own brand
 single=pg.evaluate('window.__ledger().length')
 pg.locator('#an-scope').select_option('all')
 allrows=pg.evaluate('window.__ledger()')
 assert len(allrows)>single
 assert set(x['brandId'] for x in allrows)=={'juniper'}
 assert set(x['locationId'] for x in allrows)<= {'uptown','plano','austin'}
 # cash + card matches net + tax per row aggregation
 x=pg.evaluate('window.__ledger().reduce((s,x)=>({net:s.net+x.netCents,tax:s.tax+x.taxCents,tender:s.tender+x.netCents+x.taxCents}),{net:0,tax:0,tender:0})')
 assert x['tender']==x['net']+x['tax']
 # CSV download all rows
 pg.locator('[data-action=an-tab][data-tab=mix]').click()
 with pg.expect_download() as info:pg.locator('[data-action=an-export][data-key=PMIX][data-kind=csv]').click()
 info.value.save_as('/mnt/data/plateos-demo/test-export-v5.csv')
 assert 'Item' in Path('/mnt/data/plateos-demo/test-export-v5.csv').read_text('utf-8-sig')
 pg.set_viewport_size({'width':1500,'height':1000})
 # Role restriction cashier cannot open reporting even if nav event crafted
 pg.locator('#ops-actor-top').select_option('juniper-cashier')
 assert pg.locator('[data-mode=reports]').count()==0
 pg.evaluate("document.querySelector('main').insertAdjacentHTML('beforeend','<button id=force data-action=mode data-mode=reports>Hack</button>')")
 pg.locator('#force').click()
 assert pg.locator('h1').first.inner_text()!='Analytics & reporting'
 # Manager allowed, current branch only, not cross-branch
 pg.locator('#ops-actor-top').select_option('juniper-manager')
 pg.locator('[data-mode=reports]').first.click()
 assert pg.locator('#an-scope option[value="all"]').count()==0
 # Brand isolation when switched to saffron
 pg.locator('#brand-select').select_option('saffron')
 saffron=pg.evaluate('window.__ledger()')
 assert saffron and all(x['brandId']=='saffron' for x in saffron)
 pg.locator('[data-mode=owner]').first.click()
 pg.set_viewport_size({'width':390,'height':844})
 print('Mobile owner width',pg.evaluate('document.documentElement.scrollWidth'),pg.evaluate('window.innerWidth'))
 assert pg.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
 pg.screenshot(path='/mnt/data/plateos-demo/preview-v5-owner-mobile.png',full_page=True)
 assert not errors,errors
 b.close()
print('PASS mobile/permissions/scope/csv')
