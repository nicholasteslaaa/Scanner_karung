import sqlite3
from dotenv import  load_dotenv
import  os

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

def read():
    conn = None
    try:
        conn = sqlite3.connect(DB_URL)
        
        cur = conn.cursor()
        cur.execute("SELECT * FROM infocam1 LIMIT 1")
        c1 = cur.fetchone()
        cur.execute("SELECT * FROM infocam2 LIMIT 1")
        c2 = cur.fetchone()


        cam1=(c1[1],c1[2],c1[4])
        cam2=(c2[1],c2[2],c2[4])
        return cam1,cam2

    except sqlite3.Error as e:
        print(f"A database error occurred: {e}")
    finally:
        if conn:
            conn.close()
def hitung(C1L1,C1L2,C2L1,C2L2,row1,row2):
    # 1 baris saja pasti variasi 2
    if((C1L1==C1L2==1 or C2L1==C2L2==1)  and (C1L1==2 or C2L1==2)):
        print('variasi 2')
        variasi = 2
        # print("variasi 2 hitung dr kamera yg detek 1 lapis SAJA")
        # print(f'variasi 2 lapisan samping : {len(row1)} lapisan depan :{len(row2)}')
        sisa=0
        lapis = 0
        if len(row2)==2:
            row1=row2
        else:
            pass
        for r_idx, row_objs in enumerate(row1):
            # print(f'{r_idx+1} : {len(row_objs)}')
            if (len(row_objs)==2):
                lapis+=1
            else:
                sisa+=len(row_objs)
        hasil = (lapis*2)+sisa  
        # print(lapis,sisa)
              
        sisa=0
        lapis = 0
        
        
        return hasil,variasi
    #variasi 3 -> 2,1 // 2,2  (perlu diperhatikanm cek lagi )
    if((((C1L1==2 and C1L2==1) or (C1L1==1 and C1L2==2)) and ((C2L1==2 and C2L2==2))) or (((C2L1==2 and C2L2==1) or (C2L1==1 and C2L2==2)) and ((C1L1==2 and C1L2==2))) ) :
        print('variasi 3')
        variasi = 3
        sisa=0
        lapis = 0
        if len(row2[-1])==len(row2[-2])==2:
            row1=row2
        else:
            pass
        # print(f'variasi 3 lapisan samping : {len(row1)} lapisan depan :{len(row2)}')
        for r_idx, row_objs in enumerate(row1):
            # print(f'{r_idx+1} : {len(row_objs)}')
            if (len(row_objs)==2):
                lapis+=1
            else:
                sisa+=len(row_objs)
        hasil = (lapis*3)+sisa  
        # print(lapis,sisa)      
        sisa=0
        lapis = 0
        return hasil,variasi
    #variasi 4 -> 2,2 // 2,2 (perlu diperhatikan cek lagi )
    if(C1L1==C1L2==2 and C2L1==C2L2==2):
    # if(C1L1==C2L1==2):
        
        print('variasi 4')
        variasi = 4
        
        rata=False
        sisa=0
        lapis = 0
        if (len(row1[0]))>2:
            row1[0]=[1,1]
        if (len(row2[0])>2):
            row2[0]=[1,1]
        if (len(row1[0])==(len(row2[0]))==2):
            rata = True
        
        # print(f'variasi 4 lapisan samping : {len(row1)} lapisan depan :{len(row2)}')
        for r_idx, row_objs in enumerate(row1):
            # print(f'{r_idx+1} : {len(row_objs)}')
            if (len(row_objs)==2):
                lapis+=1
            else:
                sisa+=len(row_objs)
        
        sisa=(len(row1[0])+len(row2[0]))-1
        hasil = ((lapis)*4)+sisa  
        if rata:
            hasil=lapis*4
        # print(lapis,sisa)      
        sisa=0
        lapis = 0
        return  hasil,variasi
    #variasi 5 -> 2,3 // 2,2 susah karena ditumpuk dua sekaligus
    if(((C1L1==2 and C1L2==2) and (C2L1==3 and C2L2==2 or C2L1==2 and C2L2==3 )) or ((C2L1==2 and C2L2==2) and (C1L1==3 and C1L2==2 or C1L1==2 and C1L2==3 ))  ) :
        print('variasi 5')
        variasi = 5
       
        sisa=0
        lapis = 0 
        if len(row2[0])+len(row1[0])<5:
            status_sisa =True
            r1=row1
            r2=row2
        else:
            pass
        if len(row2[-1])==len(row2[-2])==2:
            row1=row2
            
        else:
            pass
        for r_idx, row_objs in enumerate(row1):
            # print(f'{r_idx+1} : {len(row_objs)}')
            if (len(row_objs)==2):
                lapis+=1
            else:
                sisa+=len(row_objs)
        hasil = (lapis*5)+sisa 
        if status_sisa:
            sisa=(len(r1[0])+len(r2[0]))-1
            hasil = ((lapis-1)*5)+sisa 
        else:
            pass
            
                
         
        # print(lapis,sisa)      
        sisa=0
        lapis = 0        
        return  hasil,variasi
    #variasi 7 -> 3,2 // 3,3
    if((C1L1==3 and C2L1==3) or (C2L2==3 and C2L2==3)):
        print('variasi 7')
        variasi = 7        
        sisa=0
        lapis = 0
        if len(row2[-1])==len(row2[-2])==3:
            row1=row2
        else:
            pass
        for r_idx, row_objs in enumerate(row1):
            # print(f'{r_idx+1} : {len(row_objs)}')
            if (len(row_objs)==3):
                lapis+=1
            else:
                sisa+=len(row_objs)
        hasil = (lapis*7)+sisa  
        # print(lapis,sisa)      
        sisa=0
        lapis = 0
        print(hasil)
        return  hasil,variasi

    

  
# hasil_cam1, hasil_cam2 = read('db_cam1')
# print(hasil_cam1[0])