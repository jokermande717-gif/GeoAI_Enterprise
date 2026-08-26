import sys
from src.core.licensing_engine import SovereignLicenseEngine

if __name__ == "__main__":
    print("\n=======================================================")
    print("   ◬ GeoAI OVERLORD // SOVEREIGN KEY GENERATOR 2026   ")
    print("=======================================================\n")
    
    hwid = input("Geben Sie die HWID des Kunden ein (16 Zeichen): ").strip().upper()
    if len(hwid) < 8:
        print("❌ Ungültige HWID!")
        sys.exit(1)
        
    customer = input("Kunden-/Firmenname: ").strip() or "Enterprise Customer"
    valid_key = SovereignLicenseEngine.generate_valid_key(hwid, customer)
    
    print("\n✓ Generierter Lizenzschlüssel für den Kunden:")
    print("-------------------------------------------------------")
    print(f"  {valid_key}")
    print("-------------------------------------------------------")
    print("Senden Sie diesen Schlüssel an den Kunden zur Aktivierung.\n")
