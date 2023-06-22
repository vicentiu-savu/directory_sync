import logging
import shutil
import os
import filecmp
import sys
import time
from pathlib import Path

def sync_folders(source_path, replica_path, mode):
    '''Function checks the contents of the source_path(arg1) directory against the contents of the replica_path(arg3) directory. The third argument is the mode.
    'check' mode - Files/Directories not found in both locations are deleted from source directory.
    Stage 1 of folder syncronisation; the source is initialised with the path of the replica, this stage removes unwanted files.
    'copy' mode - Files/Directories not found in both locations are copied from source directory to replica directory.
    Stage 2 of folder syncronisation; the source is initialised with the path of the source, this stage copies files/directories not found in the replica directory.

    For files - function checks if a matching file is found in the replica_path directory; Deletes/Copies the file if no match is found
    For folders - 
    'check' mode: If a matching folder is not found in the replica_path directory, folder is deleted
    'copy' mode: If a matching folder is not found in the replica_path directory, folder is created
    Function calls itself for every folder in the source directory having a matching folder path in replica directory (backtracking structure).
    '''
    try:
        dir_file_list = os.listdir(source_path)
    except Exception as err:
        sync_logger.error('Directory cannot syncronised for path: ' + str(source_path) + '. Error: ' + str(err))
        return False

    for item in dir_file_list:  #iterates each item in source
        source_item_path = os.path.join(source_path,item)   
        replica_item_path = os.path.join(replica_path,item)
        try:

            if os.path.isdir(source_item_path):     #picks out only folders, not files
                if not os.path.isdir(replica_item_path):    #check if folder does not exist in replica directory. For copy mode, create folder and syncronise it, for check mode delete folder
                    if mode == 'copy':
                        try:
                            os.mkdir(replica_item_path)
                            sync_logger.info(item + ' directory not found in Replica Directory. New folder created: '+ replica_item_path)
                            sync_folders(source_item_path,replica_item_path,mode)
                        except Exception as err:
                            sync_logger.error('Directory cannot syncronised for path: ' + replica_item_path + '. Error: '+ str(err))
                    elif mode == 'check':
                        try:
                            shutil.rmtree(source_item_path)
                            sync_logger.info('Folder deleted in Replica Directory: '+ source_item_path)
                        except Exception as err:
                            sync_logger.error('Replica directory cannot be syncronised. Folder cannot be deleted for path: ' + source_item_path + '. Error: '+ str(err))               
                else:
                    sync_folders(source_item_path,replica_item_path,mode)  #if folder exist, check/copy items inside
                        
            elif os.path.isfile(source_item_path):  #picks out only files, not folders
                if not os.path.isfile(replica_item_path) or not filecmp.cmp(source_item_path, replica_item_path, shallow = True): 
                #if file does not exists (1st condition) or does not matches source_path file(2nd condition). shallow = True matches file name, date modified and size
                    if mode == 'copy':
                        try:
                            shutil.copy2(source_item_path,replica_item_path)
                            sync_logger.info('File copied from '+ source_item_path + ' to ' +replica_item_path)
                        except Exception as err:
                            sync_logger.error('File '+ source_item_path +' cannot be copied to replica folder path: ' + replica_item_path + '. Error: '+ str(err))      
                    elif mode == 'check':
                        try:
                            os.remove(source_item_path)
                            sync_logger.info('File deleted in Replica Directory: '+ source_item_path)
                        except Exception as err:
                            sync_logger.error('Replica directory cannot be syncronised. File ' + source_item_path +' cannot be deleted from replica directory. Error: '+ str(err))
        
        except Exception as err:
            sync_logger.error('Item can not be syncronised:' +source_path + '. Error:' + str(err))

    return True           

if __name__ == "__main__":

    #logger initialisation
    sync_logger = logging.getLogger('Folder syncronisation log')
    sync_logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    #console output intialisation
    sync_log_console_handler = logging.StreamHandler()
    sync_log_console_handler.setLevel(logging.DEBUG)    
    sync_log_console_handler.setFormatter(formatter)
    sync_logger.addHandler(sync_log_console_handler)
    
    #command line arguments check
    try:
        source_path = Path(os.path.abspath(sys.argv[1])) 
        replica_path = Path(os.path.abspath(sys.argv[2]))
        period = int(sys.argv[3])
        log_path = Path(os.path.abspath(sys.argv[4]))
    except Exception as err:
        sync_logger.error('Command line arguments error: ' + str(err))
        sync_logger.info('Syncronisation Stopped')
        quit()     
    
    #check log file directory path
    try:
        log_file_dir_path = os.path.dirname(log_path)            
        if not os.path.isdir(log_file_dir_path):
            sync_logger.warning('Log file directory path not found. New directory created: '+ str(log_file_dir_path))
            os.mkdir(log_file_dir_path)

        #configuration logger output file
        sync_log_file_handler = logging.FileHandler(log_path)
        sync_log_file_handler.setLevel(logging.DEBUG)
        sync_log_file_handler.setFormatter(formatter)
        sync_logger.addHandler(sync_log_file_handler)
        sync_logger.info('Syncronisation log file: '+ str(log_path))

    except Exception as err:
        sync_logger.error('Log file path error:' + str(err))
        sync_logger.info('Syncronisation Stopped')
        quit()

    #check source folder path
    try:
        if not os.path.isdir(source_path):
            sync_logger.error('Source directory not found: ' + str(source_path))
    except Exception as err:
        sync_logger.error('Source directory error for path:' + str(source_path) + '. Error:' + str(err))
        sync_logger.info('Syncronisation Stopped')
        quit()

    #check replica folder path
    try:
        if not os.path.isdir(replica_path):
            os.mkdir(replica_path)
            sync_logger.warning('Replica directory path not found. New directory created: '+ str(replica_path))
    except Exception as err:
        sync_logger.error('Replica directory error for path: ' + str(replica_path) + '. Error:' + str(err))
        sync_logger.info('Syncronisation Stopped')
        quit()
    
    #run syncronisation
    sync_logger.info('Syncronisation Started. Source directory: '+ str(source_path) + '. Replica directory: '+ str(replica_path))
    while True:
        if not sync_folders(replica_path,source_path, mode = 'check'):  #check all files in the replica folder are a copy from the source - check mode(refer to function description). Returns True / False if successful
            break  
        if not sync_folders(source_path,replica_path, mode = 'copy'):   #copy missing files from source to replica - copy mode(refer to function description). Returns True / False if successful
            break
        if max(list(sync_logger._cache.keys())) <= 30:        #check for errors during syncronisation.
            sync_logger.info('Syncronisation cycle completed successfully.')
        else:
            sync_logger.info('Syncronisation cycle completed unsuccessfully. Please check logged errors.')
        sync_logger._cache.clear()
        time.sleep(period)  #syncronisation period

    sync_logger.info('Syncronisation Stopped')
