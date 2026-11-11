# QualityLab — QA test plan

## Scope
Sistema bajo prueba: `app/shop.py`, un servicio de cotización de una tienda ficticia, expuesto por FastAPI. Este laboratorio no procesa pagos reales ni contiene autenticación corporativa.

## Acceptance criteria
1. Los productos registrados son consultables mediante `/api/shop/products`.
2. Una cotización válida devuelve subtotal, descuento y total correctos.
3. El cupón `BIENVENIDO10` aplica 10 % al subtotal y redondea a centavos.
4. Las cantidades fuera del rango 1–25, las SKU desconocidas y el stock insuficiente se rechazan.
5. La suite smoke guarda el resultado de sus seis comprobaciones en SQLite.
6. Es posible consultar y registrar una incidencia, y cambiar su estado.

## Test levels
- Unit/domain: funciones de negocio `quote_order`.
- API: endpoints con TestClient y Pytest.
- UI smoke: navegación en Chromium mediante Playwright.
- Manual exploratory: matriz de hallazgos ficticios precargada (no implica que esos errores existan en el sistema bajo prueba).
- Postman: colección opcional en `postman/` para pruebas manuales o ejecución con Newman.

## Limitations
La vista de indicadores del sprint es un dataset de demostración. No se presenta como resultado de una ejecución de una suite empresarial completa. Las pruebas reales actuales se enumeran en `tests/`.
