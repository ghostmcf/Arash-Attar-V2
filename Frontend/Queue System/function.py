from uuid import uuid4
from datetime import datetime
from os import path


def path_and_rename(pathed):
        return pathed

def path_and_rename2(pathed):  
    if pathed == "eimg":
        pathed="exam/exams/"
        def wrapper(instance, filename):
            ext = filename.split('.')[-1]
            # get filename
            if instance.pk:
                filename = '{}.{}'.format(str(instance.exam_headline), ext)
            else:
                # set filename as random string
                filename = '{}.{}'.format(uuid4().hex, ext)
            # return the whole path to the file 
            a=pathed
            a=a+instance.exam_group.name+"/"+instance.exam_headline+"/"
            return path.join(a, filename)
        return wrapper
    elif pathed == "aimg":
        pathed="exam/exams/"
        def wrapper(instance, filename):
            ext = filename.split('.')[-1]
            # get filename
            if instance.pk:
                filename = '{}.{}'.format(uuid4().hex, ext)
            else:
                # set filename as random string
                filename = '{}.{}'.format(uuid4().hex, ext)
            # return the whole path to the file 
            a=pathed
            a=a+instance.exam_group.name+"/"+instance.exam_headline+"/"+datetime.now().strftime('%Y-%m-%d')+"/"
            return path.join(a, filename)
        return wrapper
    elif pathed == "qimg":
        pathed="exam/questions/"
        def wrapper(instance, filename):
            ext = filename.split('.')[-1]
            # get filename
            if instance.pk:
                filename = '{}.{}'.format(str(instance.question_headline), ext)
            else:
                # set filename as random string
                filename = '{}.{}'.format(uuid4().hex, ext)
            # return the whole path to the file 
            a=pathed
            a=a+instance.question_category+"/"+datetime.now().strftime('%Y-%m-%d')+"/"
            return path.join(a, filename)
        return wrapper
    
    elif pathed == "aqimg":
        pathed="exam/questions/"
        def wrapper(instance, filename):
            ext = filename.split('.')[-1]
            # get filename
            if instance.pk:
                filename = '{}.{}'.format(str(instance.question_headline), ext)
            else:
                # set filename as random string
                filename = '{}.{}'.format(uuid4().hex, ext)
            # return the whole path to the file 
            a=pathed
            a=a+instance.question_category+"/"+datetime.now().strftime('%Y-%m-%d')+"/answer/"
            return path.join(a, filename)
        return wrapper
