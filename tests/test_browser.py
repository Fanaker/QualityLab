"""Real browser smoke checks of the same page bundled with the app.
For constrained environments load the page assets with set_content() (no server necessary).
"""
from pathlib import Path
import shutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]

def test_workbench_renders_and_navigates():
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True, executable_path=shutil.which("chromium") or None, args=["--no-sandbox"])
        page=browser.new_page(viewport={'width':1440,'height':900})
        html=(ROOT/'web'/'index.html').read_text(encoding='utf-8')
        css=(ROOT/'web'/'app.css').read_text(encoding='utf-8')
        js=(ROOT/'web'/'app.js').read_text(encoding='utf-8')
        # Render exactly the bundled UI with an API payload from the real FastAPI app.
        from fastapi.testclient import TestClient
        from app.main import app
        page.set_content(html.replace('<link rel="stylesheet" href="/assets/app.css">','<style>'+css+'</style>'), wait_until="domcontentloaded")
        page.evaluate('window.__BOOTSTRAP__='+__import__('json').dumps(TestClient(app).get('/api/overview').json())+';')
        page.add_script_tag(content=js)
        page.locator('text=Panel de calidad').first.wait_for()
        page.get_by_role('button',name='Casos de prueba').first.click()
        assert page.get_by_text('Biblioteca de casos').is_visible()
        browser.close()
