from playwright.sync_api import sync_playwright
from pathlib import Path
from datetime import datetime
HTML=Path('/mnt/data/plateos-demo/index.html').read_text()
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 pg=b.new_page(viewport={'width':1512,'height':1024},device_scale_factor=1)
 errors=[]
 pg.on('pageerror',lambda e:errors.append(str(e)))
 pg.route('**/*',lambda route:route.abort())
 pg.set_content(HTML,wait_until='domcontentloaded',timeout=25000)
 pg.wait_for_timeout(150)
 print('error initially',errors)
 assert not errors
 assert pg.locator('[data-action="mode"][data-mode="queue"]').count()==1
 pg.locator('[data-mode=queue]').first.click()
 print('queue header',pg.locator('h1').first.inner_text())
 assert pg.locator('.omni-order-row').count()>5
 assert 'Uber Eats' in pg.locator('main').inner_text()
 assert 'Website' in pg.locator('main').inner_text()
 pg.screenshot(path='/mnt/data/plateos-demo/preview-omni-queue.png',full_page=True)
 # Simulated inbound, force Fry station
 pg.locator('#omni-demo-channel').select_option('DoorDash')
 pg.locator('#omni-demo-item').select_option('cauliflower')
 pg.locator('[data-action=omni-inject]').click()
 injected=pg.locator('.omni-order-row').first
 print('injected',injected.inner_text()[:180])
 assert 'DoorDash' in injected.inner_text()
 oid=injected.locator('strong').first.inner_text().replace('#','')
 pg.locator('[data-action=omni-order-detail]').first.click()
 assert pg.locator('.omni-dialog').count()==1
 assert 'Fry' in pg.locator('.omni-dialog').inner_text()
 pg.screenshot(path='/mnt/data/plateos-demo/preview-omni-detail.png',full_page=True)
 pg.locator('[data-action=omni-view-kds]').click()
 assert pg.locator('h1').first.inner_text()=='Kitchen display system'
 print('station filters',pg.locator('[data-action=omni-station]').count())
 assert pg.locator('[data-action=omni-station][data-station=Fry]').count()==1
 pg.locator('[data-action=omni-station][data-station=Fry]').click()
 assert pg.locator(f'.omni-kds-card[data-kds-order="{oid}"]').count()==1
 card=pg.locator(f'.omni-kds-card[data-kds-order="{oid}"]').first
 assert 'cauliflower' in card.inner_text().lower()
 card.locator('[data-action=omni-bump]').click()
 assert pg.locator(f'.omni-kds-card[data-kds-order="{oid}"]').count()==1
 card=pg.locator(f'.omni-kds-card[data-kds-order="{oid}"]').first
 assert 'Mark ready' in card.inner_text()
 card.locator('[data-action=omni-bump]').click()
 assert 'Bump complete' in pg.locator(f'.omni-kds-card[data-kds-order="{oid}"]').inner_text()
 card=pg.locator(f'.omni-kds-card[data-kds-order="{oid}"]')
 card.locator('[data-action=omni-bump]').click()
 assert pg.locator(f'.omni-kds-card[data-kds-order="{oid}"]').count()==0
 # Multi-station isolation: seeded #1041 Grill+Bar
 pg.locator('[data-action=omni-station][data-station="All stations"]').click()
 both=pg.locator('[data-kds-order="1041"]')
 assert both.count()==2, f'Expected 2 station cards, got {both.count()}'
 pg.locator('[data-kds-order="1041"][data-kds-station="Grill"] [data-action=omni-bump]').click()
 assert pg.locator('[data-kds-order="1041"][data-kds-station="Bar"]').count()==1
 assert 'Start prep' in pg.locator('[data-kds-order="1041"][data-kds-station="Bar"]').inner_text()
 pg.screenshot(path='/mnt/data/plateos-demo/preview-omni-kds.png',full_page=True)
 # branch scoped routing controls
 pg.locator('[data-action=omni-routing-toggle]').click()
 pg.locator('select[data-omni-route="Bowls"]').select_option('Bar')
 assert 'Future Bowls tickets' in pg.locator('.toast').inner_text()
 pg.locator('[data-mode=floor]').first.click()
 assert pg.locator('.omni-floor-tile').count()==15
 print('floor ready statuses',pg.locator('.omni-floor-tile.occupied').count())
 assert 'Table 04' in pg.locator('main').inner_text()
 pg.screenshot(path='/mnt/data/plateos-demo/preview-omni-floor.png',full_page=True)
 pg.locator('[data-action=omni-open-table][data-table="04"]').first.click()
 assert pg.locator('h1').first.inner_text()=='POS register & server handheld'
 assert 'Table 04' in pg.locator('.pos-context').inner_text()
 # devices health page
 pg.locator('[data-mode=devices]').first.click()
 assert pg.locator('.omni-device-row').count()==7
 assert pg.locator('[data-action=omni-test-print]').count()==2
 assert pg.locator('[data-action=omni-test-print]:disabled').count()==0
 pg.locator('[data-action=omni-test-print]').first.click()
 assert 'simulated' in pg.locator('.toast').inner_text().lower()
 assert pg.locator('.omni-device-log').count()>=1
 pg.locator('[data-action=omni-scan-devices]').first.click()
 assert pg.locator('.omni-device-log').count()>=2
 pg.locator('#omni-device-filter').select_option('Offline only')
 assert pg.locator('.omni-device-row').count()==1
 pg.locator('[data-action=omni-toggle-device]').first.click()
 assert pg.locator('.omni-device-row').count()==0
 pg.locator('#omni-device-filter').select_option('All devices')
 assert pg.locator('.omni-device-row').count()==7
 pg.screenshot(path='/mnt/data/plateos-demo/preview-omni-devices.png',full_page=True)
 # brand / branch isolation
 pg.locator('#brand-select').select_option('saffron')
 assert pg.locator('main').inner_text().find('Dallas') == -1
 pg.locator('[data-mode=queue]').first.click()
 assert 'Zomato' in pg.locator('main').inner_text()
 assert 'DoorDash' not in pg.locator('.omni-feed').inner_text()
 pg.locator('#location-select').select_option('frisco')
 assert 'DoorDash' in pg.locator('.omni-feed').inner_text()
 assert 'Zomato' not in pg.locator('.omni-feed').inner_text()
 # Mobile view
 mobile=b.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
 mobile.route('**/*',lambda route:route.abort())
 mobile.set_content(HTML,wait_until='domcontentloaded',timeout=25000)
 mobile.locator('[data-action=side-open]').first.click()
 mobile.locator('[data-mode=queue]').first.click()
 print('mobile width',mobile.evaluate('document.documentElement.scrollWidth'),mobile.evaluate('window.innerWidth'))
 assert mobile.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
 mobile.screenshot(path='/mnt/data/plateos-demo/preview-omni-mobile.png',full_page=True)
 assert not errors,errors
 print('SUCCESS All omnichannel / KDS / floor / device tests passed')
 b.close()
