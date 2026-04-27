import psycopg2

def get_conn():
   conn = psycopg2.connect(
      host='localhost',
      user='postgres',
      database='LMS_Project_1',
      password='1234',
      port='5432'
   )
   return conn