"""
Проверка всех импортов перед сборкой
Запустите этот скрипт чтобы убедиться что все модули доступны
"""

import sys
from pathlib import Path

# Добавляем текущую директорию в path
sys.path.insert(0, str(Path(__file__).parent))

modules_to_check = [
    # External
    'tkinter',
    'PIL',
    'requests',
    'pybit.unified_trading',
    'cryptography.fernet',

    # Core
    'core.app',
    'core.auth',
    'core.events',
    'core.scheduler',

    # API
    'api.bybit_api',
    'api.master_api',
    'api.websocket_client',

    # Services
    'services.balance_service',
    'services.history_service',
    'services.order_service',
    'services.position_service',
    'services.price_service',
    'services.sync_service',
    'services.trade_service',

    # UI
    'ui.windows.login_window',
    'ui.windows.main_window',
    'ui.windows.settings_window',
    'ui.frames.history_frame',
    'ui.frames.log_frame',
    'ui.frames.orders_frame',
    'ui.frames.positions_frame',
    'ui.frames.prices_frame',
    'ui.frames.status_frame',
    'ui.widgets.loading_indicator',

    # Utils
    'utils.logger',
    'utils.validators',
    'utils.crypto',
    'utils.helpers',
    'utils.async_executor',

    # Storage
    'storage.settings',

    # Database
    'database.db',
    'database.migrations',
]

print("Checking imports...")
print("=" * 60)

failed = []
succeeded = []

for module in modules_to_check:
    try:
        __import__(module)
        print(f"✓ {module}")
        succeeded.append(module)
    except ImportError as e:
        print(f"✗ {module} - {e}")
        failed.append(module)

print("=" * 60)
print(f"\nResults:")
print(f"  Succeeded: {len(succeeded)}/{len(modules_to_check)}")
print(f"  Failed: {len(failed)}/{len(modules_to_check)}")

if failed:
    print(f"\n⚠ Failed imports:")
    for module in failed:
        print(f"  - {module}")
    print("\nPlease fix these imports before building!")
    sys.exit(1)
else:
    print("\n✓ All imports successful! Ready to build.")
    sys.exit(0)