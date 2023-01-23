import logging
import os
from flask import copy_current_request_context
import threading
from .definitions import TASK_ATTACHMENT_FOLDER, BASE_STORAGE_FOLDER, STATIC_FILES_FOLDER, CHUNK_SIZE, PUBLIC_FOLDER
from deta import Deta
import mimetypes


class StorageHandler(object):

    def __init__(self):
        
        self.proj_key = os.environ['DETA_PROJECT_KEY']
        self.deta = Deta(self.proj_key)
        self.base_storage_folder = BASE_STORAGE_FOLDER

        self.client = self.deta.Drive(self.base_storage_folder)

    def uploadPublicFiles(self):
        files = os.listdir('core/static_files/')
        for file in files:
            self.client.put("/".join([PUBLIC_FOLDER, file]), path = 'core/static_files/' + file)

    def upload(self, file, task_id, object_name):

        try:
            self.client.put("/".join([TASK_ATTACHMENT_FOLDER, task_id, object_name]), data = file)
            
        except Exception as e:
            logging.error(e)
            raise e
    
    def getLink(self, category, entity, resource_name, expiration=3600): 
        link = "/".join(
            [os.environ['YELL_MAIN_URL'], 
            STATIC_FILES_FOLDER, 
            category, 
            entity, resource_name])
        return link
    
    def get(self, category = None, entity = None, resource_name = None): 
        path_list = list(filter(lambda x: x is not None, [category, entity, resource_name]))
        try:
            response = self.client.get("/".join(path_list))
            while 1:
                buf = response.read(CHUNK_SIZE)
                if buf:
                    yield buf
                else:
                    break
        except Exception as e:
            logging.error(e)
            return None
    
    def getMime(self, path): 
        mime = mimetypes.guess_type(path)[0]
        if mime is None:
            mime = '*/*'
        return mime
    
    def delete(self, task_id, object_name):
        try:
            self.client.delete("/".join([TASK_ATTACHMENT_FOLDER, task_id, object_name]))
        except Exception as e:
            logging.error(e)
            return False
        return True

    def uploadAsync(self, file, task_id, object_name):
        @copy_current_request_context
        def uploadFile(file, task_id, object_name):
            self.upload(file, task_id, object_name)

        sender = threading.Thread(name='uploader', target=uploadFile, args=(file, task_id, object_name,))
        sender.start()