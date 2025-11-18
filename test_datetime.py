from datetime import datetime
from pydantic import BaseModel

class Test(BaseModel):
    dt: datetime

# Probar con formato Z
try:
    t = Test(dt='2024-01-15T10:30:00Z')
    print(f"✓ Formato Z funciona: {t.dt}")
except Exception as e:
    print(f"✗ Formato Z falla: {e}")

# Probar sin Z
try:
    t2 = Test(dt='2024-01-15T10:30:00')
    print(f"✓ Formato sin Z funciona: {t2.dt}")
except Exception as e:
    print(f"✗ Formato sin Z falla: {e}")
