import sqlite3

def main():
    conn = sqlite3.connect('inventory.db')
    cur = conn.cursor()
    try:
        cur.execute('''SELECT batch_id, file_name, uploaded_by, total_records, success_records, failed_records, status, upload_date FROM upload_history ORDER BY batch_id DESC LIMIT 10''')
        rows = cur.fetchall()
        for r in rows:
            print(r)
    except Exception as e:
        print('ERR', e)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
