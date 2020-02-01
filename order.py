
from dataclasses import dataclass

@dataclass
class Order:
    region: str
    server: str
    faction: str
    stock: int
    currency: str
    description: str
    min_unit_per_order: int
    duration: int
    delivery_option: str
    online_hrs: int
    offline_hrs: int