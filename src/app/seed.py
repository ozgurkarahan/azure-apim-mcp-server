"""Seed the database with ST Micro themed data."""
import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select, func

from src.app.database import engine, async_session, Base
from src.app.models import Customer, Product, Order, OrderItem, OrderStatus


CUSTOMERS = [
    {"company_name": "TechFusion GmbH", "contact_name": "Klaus Weber", "contact_email": "k.weber@techfusion.de", "phone": "+49-89-555-0101", "address": "Maximilianstraße 35", "city": "Munich", "country": "Germany"},
    {"company_name": "Sakura Electronics Co.", "contact_name": "Yuki Tanaka", "contact_email": "y.tanaka@sakuraelec.jp", "phone": "+81-3-5555-0202", "address": "2-4-1 Marunouchi", "city": "Tokyo", "country": "Japan"},
    {"company_name": "Sierra Circuits Inc.", "contact_name": "Emily Chen", "contact_email": "e.chen@sierracircuits.com", "phone": "+1-408-555-0303", "address": "1850 Technology Dr", "city": "San Jose", "country": "USA"},
    {"company_name": "HanBit Semiconductor", "contact_name": "Min-jun Park", "contact_email": "mjpark@hanbitsemi.kr", "phone": "+82-2-555-0404", "address": "231 Teheran-ro", "city": "Seoul", "country": "South Korea"},
    {"company_name": "Shenzhen IoT Solutions", "contact_name": "Wei Zhang", "contact_email": "w.zhang@sziot.cn", "phone": "+86-755-555-0505", "address": "88 Keyuan Road, Nanshan", "city": "Shenzhen", "country": "China"},
    {"company_name": "Cambridge Embedded Systems", "contact_name": "James O'Brien", "contact_email": "j.obrien@cambridgeembedded.co.uk", "phone": "+44-1223-555-0606", "address": "15 Station Road", "city": "Cambridge", "country": "UK"},
    {"company_name": "Lyon Automatismes SAS", "contact_name": "Pierre Dubois", "contact_email": "p.dubois@lyonauto.fr", "phone": "+33-4-555-0707", "address": "42 Rue de la République", "city": "Lyon", "country": "France"},
    {"company_name": "Milano Robotica S.r.l.", "contact_name": "Giulia Rossi", "contact_email": "g.rossi@milanorobotica.it", "phone": "+39-02-555-0808", "address": "Via Torino 25", "city": "Milan", "country": "Italy"},
    {"company_name": "Nordic Sensor AB", "contact_name": "Erik Lindqvist", "contact_email": "e.lindqvist@nordicsensor.se", "phone": "+46-8-555-0909", "address": "Sveavägen 44", "city": "Stockholm", "country": "Sweden"},
    {"company_name": "Maple Leaf Electronics", "contact_name": "Sarah Thompson", "contact_email": "s.thompson@mapleleafelectronics.ca", "phone": "+1-613-555-1010", "address": "350 Albert St", "city": "Ottawa", "country": "Canada"},
]

PRODUCTS = [
    # MCUs - STM32F4
    {"part_number": "STM32F407VGT6", "name": "STM32F407 MCU 168MHz 1MB Flash", "description": "ARM Cortex-M4 with FPU, 168 MHz, 1MB Flash, 192KB SRAM, USB OTG", "category": "Microcontrollers", "family": "STM32F4", "unit_price": Decimal("8.5200"), "stock_quantity": 15000, "lead_time_days": 12},
    {"part_number": "STM32F446RET6", "name": "STM32F446 MCU 180MHz 512KB Flash", "description": "ARM Cortex-M4 with FPU, 180 MHz, 512KB Flash, 128KB SRAM", "category": "Microcontrollers", "family": "STM32F4", "unit_price": Decimal("6.7500"), "stock_quantity": 22000, "lead_time_days": 10},
    {"part_number": "STM32F411CEU6", "name": "STM32F411 MCU 100MHz 512KB Flash", "description": "ARM Cortex-M4 with FPU, 100 MHz, 512KB Flash, 128KB SRAM, low power", "category": "Microcontrollers", "family": "STM32F4", "unit_price": Decimal("3.9800"), "stock_quantity": 35000, "lead_time_days": 8},
    # MCUs - STM32L4
    {"part_number": "STM32L476RGT6", "name": "STM32L476 Ultra-Low-Power MCU", "description": "ARM Cortex-M4 with FPU, 80 MHz, 1MB Flash, ultra-low-power", "category": "Microcontrollers", "family": "STM32L4", "unit_price": Decimal("7.2000"), "stock_quantity": 18000, "lead_time_days": 14},
    {"part_number": "STM32L432KCU6", "name": "STM32L432 Ultra-Low-Power MCU", "description": "ARM Cortex-M4, 80 MHz, 256KB Flash, ultra-low-power, UFQFPN32", "category": "Microcontrollers", "family": "STM32L4", "unit_price": Decimal("4.1500"), "stock_quantity": 28000, "lead_time_days": 10},
    # MCUs - STM32H7
    {"part_number": "STM32H743ZIT6", "name": "STM32H743 High-Performance MCU", "description": "ARM Cortex-M7 with FPU, 480 MHz, 2MB Flash, 1MB SRAM", "category": "Microcontrollers", "family": "STM32H7", "unit_price": Decimal("14.3500"), "stock_quantity": 8000, "lead_time_days": 18},
    {"part_number": "STM32H750VBT6", "name": "STM32H750 Value Line MCU", "description": "ARM Cortex-M7, 480 MHz, 128KB Flash, 1MB SRAM, value line", "category": "Microcontrollers", "family": "STM32H7", "unit_price": Decimal("5.8000"), "stock_quantity": 12000, "lead_time_days": 14},
    # MCUs - STM32G0
    {"part_number": "STM32G071RBT6", "name": "STM32G071 Entry-Level MCU", "description": "ARM Cortex-M0+, 64 MHz, 128KB Flash, USB-C PD controller", "category": "Microcontrollers", "family": "STM32G0", "unit_price": Decimal("2.4500"), "stock_quantity": 45000, "lead_time_days": 8},
    {"part_number": "STM32G030F6P6", "name": "STM32G030 Baseline MCU", "description": "ARM Cortex-M0+, 64 MHz, 32KB Flash, cost-effective", "category": "Microcontrollers", "family": "STM32G0", "unit_price": Decimal("0.7800"), "stock_quantity": 100000, "lead_time_days": 6},
    # MCUs - STM8S
    {"part_number": "STM8S003F3P6", "name": "STM8S003 8-bit MCU", "description": "8-bit MCU, 16 MHz, 8KB Flash, 1KB SRAM, low cost", "category": "Microcontrollers", "family": "STM8S", "unit_price": Decimal("0.3200"), "stock_quantity": 200000, "lead_time_days": 6},
    # MEMS Sensors
    {"part_number": "LIS3DHTR", "name": "LIS3DH 3-axis Accelerometer", "description": "MEMS digital output motion sensor, ultra-low-power, ±2g/±4g/±8g/±16g", "category": "MEMS Sensors", "family": "LIS", "unit_price": Decimal("1.1500"), "stock_quantity": 50000, "lead_time_days": 8},
    {"part_number": "LSM6DSOTR", "name": "LSM6DSO IMU 6-axis", "description": "iNEMO inertial module: 3D accelerometer + 3D gyroscope, AI-enhanced", "category": "MEMS Sensors", "family": "LSM", "unit_price": Decimal("2.8500"), "stock_quantity": 30000, "lead_time_days": 10},
    {"part_number": "LPS22HHTR", "name": "LPS22HH Pressure Sensor", "description": "MEMS nano pressure sensor, 260-1260 hPa absolute digital barometer", "category": "MEMS Sensors", "family": "LPS", "unit_price": Decimal("2.1000"), "stock_quantity": 25000, "lead_time_days": 10},
    {"part_number": "HTS221TR", "name": "HTS221 Humidity & Temp Sensor", "description": "Capacitive digital sensor for relative humidity and temperature", "category": "MEMS Sensors", "family": "HTS", "unit_price": Decimal("1.6500"), "stock_quantity": 40000, "lead_time_days": 8},
    {"part_number": "LSM303AGRTR", "name": "LSM303AGR eCompass", "description": "Ultra-compact 3D accelerometer + 3D magnetometer module", "category": "MEMS Sensors", "family": "LSM", "unit_price": Decimal("1.9500"), "stock_quantity": 20000, "lead_time_days": 12},
    # Power MOSFETs
    {"part_number": "STF16N65M5", "name": "N-channel 650V 12A MOSFET", "description": "MDmesh M5 series, N-channel 650V, 12A, SuperMESH5 power MOSFET", "category": "Power MOSFETs", "family": "STF", "unit_price": Decimal("1.8500"), "stock_quantity": 20000, "lead_time_days": 10},
    {"part_number": "STD10NF10", "name": "N-channel 100V 13A MOSFET", "description": "N-channel 100V, 0.065 ohm, 13A, DPAK power MOSFET", "category": "Power MOSFETs", "family": "STD", "unit_price": Decimal("0.6500"), "stock_quantity": 60000, "lead_time_days": 8},
    # Power Management
    {"part_number": "L7805CV", "name": "L7805 5V Voltage Regulator", "description": "Positive voltage regulator, 5V, 1.5A, TO-220", "category": "Power Management", "family": "L78", "unit_price": Decimal("0.4200"), "stock_quantity": 150000, "lead_time_days": 6},
    {"part_number": "L7812CV", "name": "L7812 12V Voltage Regulator", "description": "Positive voltage regulator, 12V, 1.5A, TO-220", "category": "Power Management", "family": "L78", "unit_price": Decimal("0.4500"), "stock_quantity": 120000, "lead_time_days": 6},
    {"part_number": "ST1S10PHR", "name": "ST1S10 3A Step-Down Converter", "description": "3A, 900 kHz synchronous step-down switching regulator", "category": "Power Management", "family": "ST1S", "unit_price": Decimal("1.3500"), "stock_quantity": 35000, "lead_time_days": 10},
    # Motor Drivers
    {"part_number": "L6234PD013TR", "name": "L6234 BLDC Motor Driver", "description": "Three-phase motor driver, 4A peak, 52V max", "category": "Motor Drivers", "family": "L6", "unit_price": Decimal("3.9500"), "stock_quantity": 15000, "lead_time_days": 14},
    {"part_number": "L298N", "name": "L298N Dual Full-Bridge Driver", "description": "Dual full-bridge motor driver, 46V, 2A per channel", "category": "Motor Drivers", "family": "L298", "unit_price": Decimal("3.4500"), "stock_quantity": 25000, "lead_time_days": 10},
    # Wireless
    {"part_number": "BLUENRG-M2SP", "name": "BlueNRG-M2 BLE Module", "description": "Bluetooth Low Energy 5.2 network processor module", "category": "Wireless", "family": "BlueNRG", "unit_price": Decimal("4.7500"), "stock_quantity": 10000, "lead_time_days": 16},
    {"part_number": "BLUENRG-355MC", "name": "BlueNRG-LP BLE SoC", "description": "Bluetooth Low Energy 5.4 wireless SoC, ARM Cortex-M0+", "category": "Wireless", "family": "BlueNRG", "unit_price": Decimal("3.2000"), "stock_quantity": 18000, "lead_time_days": 14},
    # Op-Amps
    {"part_number": "TSV911AILT", "name": "TSV911 Rail-to-Rail Op-Amp", "description": "Rail-to-rail I/O operational amplifier, 8 MHz, low noise", "category": "Analog", "family": "TSV", "unit_price": Decimal("0.5500"), "stock_quantity": 80000, "lead_time_days": 8},
    {"part_number": "TSH82IDT", "name": "TSH82 Dual High-Speed Op-Amp", "description": "Dual high-speed current feedback op-amp, 200 MHz", "category": "Analog", "family": "TSH", "unit_price": Decimal("1.2500"), "stock_quantity": 30000, "lead_time_days": 10},
    # Extra MCU
    {"part_number": "STM32F103C8T6", "name": "STM32F103 BluePill MCU", "description": "ARM Cortex-M3, 72 MHz, 64KB Flash, 20KB SRAM, popular dev board MCU", "category": "Microcontrollers", "family": "STM32F1", "unit_price": Decimal("2.1500"), "stock_quantity": 55000, "lead_time_days": 8},
    {"part_number": "STM32WB55CGU6", "name": "STM32WB55 Dual-Core BLE MCU", "description": "Dual-core ARM Cortex-M4/M0+, BLE 5.4, 802.15.4, 1MB Flash", "category": "Microcontrollers", "family": "STM32WB", "unit_price": Decimal("6.2000"), "stock_quantity": 14000, "lead_time_days": 16},
]


async def seed_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # Check if data exists
        result = await db.execute(select(func.count()).select_from(Customer))
        if result.scalar_one() > 0:
            print("Database already seeded, skipping.")
            return

        print("Seeding database...")

        # Create customers
        customers = []
        for c_data in CUSTOMERS:
            customer = Customer(id=uuid.uuid4(), **c_data)
            db.add(customer)
            customers.append(customer)
        await db.flush()

        # Create products
        products = []
        for p_data in PRODUCTS:
            product = Product(id=uuid.uuid4(), **p_data)
            db.add(product)
            products.append(product)
        await db.flush()

        # Create orders
        now = datetime.now(timezone.utc)
        status_weights = [
            (OrderStatus.delivered, 0.30),
            (OrderStatus.shipped, 0.25),
            (OrderStatus.processing, 0.20),
            (OrderStatus.confirmed, 0.15),
            (OrderStatus.pending, 0.10),
        ]
        statuses = [s for s, _ in status_weights]
        weights = [w for _, w in status_weights]

        order_count = 0
        for i in range(40):
            status = random.choices(statuses, weights=weights, k=1)[0]
            customer = random.choice(customers)
            days_ago = random.randint(1, 180)
            ordered_at = now - timedelta(days=days_ago)
            month_str = ordered_at.strftime("%Y%m")
            order_count += 1
            order_number = f"ST-ORD-{month_str}-{order_count:04d}"

            shipped_at = None
            delivered_at = None
            if status in (OrderStatus.shipped, OrderStatus.delivered):
                shipped_at = ordered_at + timedelta(days=random.randint(2, 7))
            if status == OrderStatus.delivered:
                delivered_at = shipped_at + timedelta(days=random.randint(1, 5))

            order = Order(
                id=uuid.uuid4(),
                order_number=order_number,
                customer_id=customer.id,
                status=status,
                total_amount=Decimal("0.00"),
                currency="USD",
                shipping_address=f"{customer.address}, {customer.city}, {customer.country}",
                ordered_at=ordered_at,
                shipped_at=shipped_at,
                delivered_at=delivered_at,
            )
            db.add(order)
            await db.flush()

            # Add 1-5 items
            num_items = random.randint(1, 5)
            selected_products = random.sample(products, min(num_items, len(products)))
            total = Decimal("0.00")
            for product in selected_products:
                qty = random.randint(50, 5000)
                line_total = product.unit_price * qty
                total += line_total
                item = OrderItem(
                    id=uuid.uuid4(),
                    order_id=order.id,
                    product_id=product.id,
                    quantity=qty,
                    unit_price=product.unit_price,
                    line_total=line_total,
                )
                db.add(item)

            order.total_amount = total

        await db.commit()
        print(f"Seeded {len(customers)} customers, {len(products)} products, 40 orders.")


if __name__ == "__main__":
    asyncio.run(seed_database())
