from uuid import uuid4
from datetime import datetime
from os import path


def path_and_rename2(pathed):
        return pathed

def path_and_rename(pathed):  
    if pathed == "assignment_file":
        pathed= "assignment/files/"
        def wrapper(instance, filename):
            ext = filename.split('.')[-1]
            # get filename
            if instance.pk:
                filename = '{}.{}'.format(str(instance.assignment_headline), ext)
            else:
                # set filename as random string
                filename = '{}.{}'.format(uuid4().hex, ext)
            # return the whole path to the file 
            a=pathed
            a=a+str(datetime.now().year)+"-"+str(datetime.now().month)+"/"+instance.assignment_group.name+"/"
            return path.join(a, filename)
        return wrapper
    elif pathed == "assignment_answer_file":
        pathed= "assignment/files/"
        def wrapper(instance, filename):
            ext = filename.split('.')[-1]
            # get filename
            if instance.pk:
                filename = '{}.{}'.format(str(instance.assignment_headline)+"ANS", ext)
            else:
                # set filename as random string
                filename = '{}.{}'.format(uuid4().hex, ext)
            # return the whole path to the file 
            a=pathed
            a=a+str(datetime.now().year)+"-"+str(datetime.now().month)+"/"+instance.assignment_group.name+"/"
            return path.join(a, filename)
        return wrapper
    elif pathed == "assignment/students/":
        def wrapper(instance, filename):
            ext = filename.split('.')[-1]
            # get filename
            if instance.pk:
                filename = '{}.{}'.format(str(instance.assignment_average_reffer.user.username), ext)
            else:
                # set filename as random string
                filename = '{}.{}'.format(uuid4().hex, ext)
            # return the whole path to the file 
            a=pathed
            a=a+instance.assignment.assignment_group.name+"/"+instance.assignment.assignment_headline+"/"
            return path.join(a, filename)
        return wrapper
    elif pathed == "assignment/students/answers/":
        def wrapper(instance, filename):
            ext = filename.split('.')[-1]
            # get filename
            if instance.pk:
                filename = '{}.{}'.format(str(instance.assignment_average_reffer.user.username)+"-Marked", ext)
            else:
                # set filename as random string
                filename = '{}.{}'.format(uuid4().hex, ext)
            # return the whole path to the file 
            a=pathed
            a=a+instance.assignment.assignment_group.name+"/"+instance.assignment.assignment_headline+"/"
            return path.join(a, filename)
        return wrapper
    elif pathed == "eimg":
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
        
    # elif pathed == "cimg":
    #     pathed="exam/choices/"
    #     def wrapper(instance, filename):
    #         ext = filename.split('.')[-1]
    #         # get filename
    #         if instance.pk:
    #             filename = '{}.{}'.format(str(instance.choice_text), ext)
    #         else:
    #             # set filename as random string
    #             filename = '{}.{}'.format(uuid4().hex, ext)
    #         # return the whole path to the file 
    #         a=pathed
    #         a=a+instance.question.exam.exam_group.name+"/"+instance.question.exam.exam_headline+"/"+instance.question.question_headline+"/"
    #         return path.join(a, filename)
    #     return wrapper
    elif pathed == "useravatar/":
        def wrapper(instance, filename):
            ext = filename.split('.')[-1]
            # get filename
            if instance.pk:
                filename = '{}.{}'.format(str(instance.student_user), ext)
            else:
                # set filename as random string
                filename = '{}.{}'.format(uuid4().hex, ext)
            # return the whole path to the file 
            a=pathed
            # a=a+str(instance.student_user.groups.all()[0].id)+"/"
            a=a+instance.student_user.groups.all()[0].name+"/"
            return path.join(a, filename)
        return wrapper
    elif pathed == "userscoresheet/":
        def wrapper(instance, filename):
            ext = filename.split('.')[-1]
            # get filename
            if instance.pk:
                filename = '{}.{}'.format(str(instance.student_user), ext)
            else:
                # set filename as random string
                filename = '{}.{}'.format(uuid4().hex, ext)
            # return the whole path to the file 
            a=pathed
            # a=a+str(instance.student_user.groups.all()[0].id)+"/"
            a=a+instance.student_user.groups.all()[0].name+"/"
            return path.join(a, filename)
        return wrapper
