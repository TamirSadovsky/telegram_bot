import pyodbc

# Database connection details
server = "81.218.80.23\\WIZSOFT,7002"  # Use instance name and port
database = "RamTest"
username = "sa"
password = "wizsoft"

try:
    # Connect to SQL Server
    conn = pyodbc.connect(
        f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}",
        timeout=5
    )
    cursor = conn.cursor()
    print("✅ Connected to SQL Server!")

    # Execute stored procedure
    cursor.execute("{CALL FindArea}")  # Call the stored procedure

    # Fetch first row
    row = cursor.fetchone()

    if row:
        print(f"AreaDes: {row.AreaDes}, AreaID: {row.AreaID}")
    else:
        print("⚠ No data returned.")

    # Close connection
    cursor.close()
    conn.close()

except Exception as e:
    print("❌ Connection failed:", e)
