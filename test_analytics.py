from pathlib import Path
from playwright.sync_api import sync_playwright
HTML=Path('/mnt/data/plateos-demo/index.html').read_text().replace('    render();\n  })();','    window.__v5DB=()=>JSON.parse(JSON.stringify(db));window.__v5Reports=()=>anDataset(anGroup);window.__v5Rows=()=>anRows();render();\n  })();')
with sync_playwright() as pw:
 b=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 pg=b.new_page(viewport={'width':1500,'height':1000},device_scale_factor=1,accept_downloads=True)
 pg.route('https://**/*',lambda r:r.abort())
 errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
 pg.set_content(HTML,wait_until='domcontentloaded',timeout=30000)
 print('title',pg.title(),'errors',errors[:5])
 assert not errors, errors
 assert pg.locator('[data-mode=reports]').count()>0
 pg.locator('[data-mode=reports]').first.click()
 assert pg.locator('h1').inner_text()=='Analytics & reporting'
 print('reports',pg.locator('main').inner_text()[:260])
 pg.screenshot(path='/mnt/data/plateos-demo/preview-v5-analytics.png',full_page=True)
 print('Rows',len(pg.evaluate('window.__v5Rows()')))
 pg.locator('[data-action=an-prompt]').first.click()
 print('ask result',pg.locator('.an-ai-answer').inner_text()[:330])
 assert 'Lunch net sales' in pg.locator('.an-ai-answer').inner_text()
 pg.locator('[data-action=an-tab][data-tab=mix]').click()
 pg.screenshot(path='/mnt/data/plateos-demo/preview-v5-pmix.png',full_page=True)
 pg.locator('[data-action=an-tab][data-tab=exceptions]').click()
 pg.screenshot(path='/mnt/data/plateos-demo/preview-v5-exceptions.png',full_page=True)
 pg.locator('[data-action=an-tab][data-tab=builder]').click()
 pg.locator('#an-group').select_option('Payment Type')
 pg.locator('#an-template-name').fill('Weekly payment reconciliation')
 pg.locator('[data-action=an-save-template]').click()
 assert len(pg.evaluate('window.__v5DB().analyticsTemplates'))==1
 pg.locator('#an-email').fill('books@example.com')
 pg.locator('[data-action=an-save-schedule]').click()
 assert pg.evaluate('window.__v5DB().analyticsTemplates[0].schedule.email')=='books@example.com'
 print('schedule',pg.evaluate('window.__v5DB().analyticsTemplates[0].schedule'))
 with pg.expect_download() as dl:
  pg.locator('[data-action=an-export][data-key=builder][data-kind=xlsx]').click()
 download=dl.value;print('download',download.suggested_filename)
 download.save_as('/mnt/data/plateos-demo/test-export-v5.xlsx')
 pg.screenshot(path='/mnt/data/plateos-demo/preview-v5-builder.png',full_page=True)
 pg.locator('[data-action=an-tab][data-tab=closings]').click()
 pg.locator('#an-count').fill('320.00')
 pg.locator('[data-action=an-x-report]').click()
 assert 'X-Report' in pg.locator('.an-report-sheet').inner_text()
 pg.locator('[data-action=an-close-dialog]').first.click()
 pg.locator('[data-action=an-z-report]').click()
 pg.locator('[data-action=an-confirm-z]').click()
 assert len(pg.evaluate('window.__v5DB().analyticsClosings'))==1
 pg.locator('[data-action=an-batch]').click()
 assert len(pg.evaluate('window.__v5DB().analyticsBatchEvents'))==1
 pg.screenshot(path='/mnt/data/plateos-demo/preview-v5-closeout.png',full_page=True)
 pg.locator('[data-mode=owner]').first.click()
 pg.screenshot(path='/mnt/data/plateos-demo/preview-v5-owner.png',full_page=True)
 print('owner',pg.locator('h1').inner_text(), 'phone',pg.locator('.an-phone').inner_text()[:240])
 pg.locator('#brand-select').select_option('saffron')
 assert pg.locator('.an-phone').count()==1
 assert 'Saffron' in pg.locator('.an-phone').inner_text()
 assert not errors,errors
 b.close()
print('PASS')
