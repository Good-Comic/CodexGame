const assert = require('node:assert/strict');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/chromium', headless: true });
  const page = await browser.newPage();
  const consoleErrors = [];
  page.on('console', message => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('pageerror', error => consoleErrors.push(error.message));
  try {
    const response = await page.goto('http://127.0.0.1:8080/preview/preview-demo/');
    assert.equal(response.status(), 200);
    assert.equal(await page.title(), 'Project Forge Preview Demo');
    assert.equal(await page.locator('#language option').count(), 4);
    await page.selectOption('#language', 'ja');
    await page.click('#start');
    assert.equal(await page.locator('#status').textContent(), 'Running (ja)');
    assert.deepEqual(consoleErrors, []);
    await page.screenshot({ path: '/tmp/project-forge-preview-smoke.png' });
    console.log('preview smoke: PASS (HTTP 200, 4 languages, start action, no console errors)');
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
