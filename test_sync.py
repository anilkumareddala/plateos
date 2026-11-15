from playwright.sync_api import sync_playwright
from pathlib import Path
s=Path('/mnt/data/plateos-demo/index.html').read_text()
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 page=b.new_page(viewport={'width':1370,'height':850});errs=[];page.on('pageerror',lambda e:errs.append(str(e)))
 page.route('**/*',lambda r:r.abort());page.set_content(s,wait_until='domcontentloaded',timeout=30000)
 page.locator('[data-action=mode][data-mode=pos]').click()
 page.locator('[data-action=pos-service][data-service="Dine in"]').click()
 page.locator('[data-action=pos-table-open][data-table="06"]').click()
 page.locator('[data-action=pos-offline]').first.click()
 page.locator('[data-action=item][data-id="smash-burger"]').click()
 page.locator('[name=required]').first.check()
 page.locator('#pos-item-note').fill('Allergy: gluten')
 page.locator('[data-action=modal-add]').click()
 page.locator('[data-action=pos-send]').click()
 assert '1 queued' in page.locator('.pos-offline-banner').inner_text()
 page.locator('[data-action=mode][data-mode=kds]').first.click()
 assert page.locator('.omni-kds-card').filter(has_text='Table 06').count()==0
 page.locator('[data-action=mode][data-mode=pos]').click()
 page.locator('[data-action=pos-offline]').first.click()
 page.locator('[data-action=mode][data-mode=kds]').first.click()
 assert page.locator('.omni-kds-card').filter(has_text='Table 06').count()==1
 assert page.locator('.omni-kds-card').filter(has_text='Allergy: gluten').count()==1
 page.locator('[data-action=mode][data-mode=pos]').click()
 page.locator('#location-select').select_option('plano')
 page.locator('[data-action=pos-service][data-service="Dine in"]').click()
 assert page.locator('.pos-check-option').count()==0
 print('PASS: offline queue → reconnect → exactly-one KDS ticket with note; location scoped; no JS errors',errs)
 b.close()
