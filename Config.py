import os

def config():
  UPLOAD_FOLDER=os.environ.get('UPLOAD_FOLDER',os.path.join(os.getcwd(),'Upload'))
  