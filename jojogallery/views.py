from django.shortcuts import render,HttpResponse,redirect
from django.http import FileResponse
import os
from django.http import Http404, StreamingHttpResponse
from django import views
from jojogallery import models
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
def auth(func):
    def inner(req,*args,**kwargs):
        login_logo=req.session.get('is_login')
        if login_logo:
            return func(req,*args,**kwargs)
        else:
            return redirect('/login.html')
    return inner
class login(views.View):
    def get(self,req,*args,**kwargs):
        return render(req,'login.html')
    def post(self,req,*args,**kwargs):
        username=req.POST.get('username')
        password=req.POST.get('password')
        print(username,password)
        result=models.user.objects.filter(username=username,password=password).first()
        import json
        if result:
            req.session['username']=username
            req.session['is_login']=True
            req.session['id']=result.id
            req.session['permission']=result.permission
            return redirect('/search.html')
        else:
            msg='用户名或密码错误'
            return render(req,'login.html',{'msg':msg})
@method_decorator(auth,name='dispatch')
class member(views.View):
    def get(self,req,*args,**kwargs):
        apart_id=req.GET.get('nid')
        print(apart_id)
        username=req.session.get('username')
        userid=req.session.get('id')
        user_permission=req.session.get('permission')
        member_obj=models.imgDetail.objects.filter(apartment_id=apart_id)
        member_obj1=models.imgApartMent.objects.filter(id=apart_id).first()
        current_page = req.GET.get('p', 1)
        current_page = int(current_page)
        # 所有数据的个数
        total_count = member_obj.count()

        exp_pages = 15
        if total_count <= exp_pages:
            return render(req, 'member.html',
                          {'username': username, 'member_obj': member_obj, 'member_obj1': member_obj1,
                           'user_permission': user_permission})
        from utils.page import PageHelper

        obj = PageHelper.PagerHelper1(total_count, current_page, '/member.html/?nid=%s'%apart_id, exp_pages)
        pager = obj.pager_str()

        cls_list = member_obj[obj.db_start:obj.db_end]

        return render(req,'member.html',{'str_pager': pager,'username':username,'member_obj':cls_list,'member_obj1':member_obj1,'user_permission':user_permission})
    def post(self,req,*args,**kwargs):
        import json
        nid=req.POST.get('nid')
        content=req.POST.get('content')
        if content=='delete':
            todel_obj = models.imgDetail.objects.filter(id=nid).first()
            toDel_path=todel_obj.folder
            models.imgDetail.objects.filter(id=nid).delete()
            import os
            import shutil
            shutil.rmtree(toDel_path)
            return HttpResponse(json.dumps('ok'))
        else:
            if content:
                models.imgDetail.objects.filter(id=nid).update(caption=content)
                return HttpResponse(json.dumps('ok'))
            else:
                return HttpResponse(json.dumps('no'))
# Create your views here.
@method_decorator(auth,name='dispatch')
class general_view(views.View):
    def get(self,req,*args,**kwargs):
        username = req.session.get('username')
        user_permission = req.session.get('permission')
        nid=req.GET.get('nid')
        img_obj=models.imgUrl.objects.filter(iCaption__id=nid).order_by('-idate')
        detail_obj=models.imgDetail.objects.filter(id=nid).first()
        from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
        paginator = Paginator(img_obj, 5)  # 每页两条数据
        page = req.GET.get('page', 1)  # QueryDict objects,如果没有对应的page键，就返回默认1。
        item_info = paginator.page(page)  # 根据索引page，返回该page数据，如果不存在，引起 InvalidPage异常

        try:
            cls_list = paginator.page(page)
        except PageNotAnInteger:

            cls_list = paginator.page(1)
        except EmptyPage:

            cls_list = paginator.page(paginator.num_pages)
        current_user = req.session.get('username')

        return render(req,'general_view.html',{'nid':nid,'item_info': item_info,'detail_obj':detail_obj,'username':username,'img_obj':img_obj,'cls_list':cls_list,'user_permission':user_permission})
    def post(self,req,*args,**kwargs):
        flag=req.POST.get('flag')
        if flag=='check':
            ischecked=req.POST.get('ischeck')
            if ischecked=='true':
                ischecked=True
            else:
                ischecked=False
            nid=req.POST.get('nid')
            models.imgUrl.objects.filter(id=nid).update(iChecked=ischecked)
            img_obj_download = models.imgUrl.objects.filter(iChecked=1)
            checked_list=[]
            for item in img_obj_download:
                checked_list.append(item.iname)
            import json
            return HttpResponse(json.dumps(checked_list))
        elif flag=='pre':
            nid=req.POST.get('nid')
            print(nid)
            detail_id=req.POST.get('detail_id')
            print(detail_id)
            pre_obj=models.imgUrl.objects.filter(id__lt=nid,iCaption=detail_id).last()
            print(pre_obj)
            if pre_obj:
                check = pre_obj.iChecked
                obj_type = pre_obj.iDevice
                macro_url='\\'+str(pre_obj.iurl[obj_type])
                alex=pre_obj.id
                caption_iname=pre_obj.iname
                pre_dict={'valid':True,'alex':alex,'macro_url':macro_url,'checkee':check,'iname':caption_iname}
                import json
                return HttpResponse(json.dumps(pre_dict))
            else:
                pre_dict = {'valid': False, 'alex': None, 'macro_url': None}
                import json
                return HttpResponse(json.dumps(pre_dict))
        elif flag=='next':
            nid=req.POST.get('nid')
            detail_id=req.POST.get('detail_id')
            next_obj=models.imgUrl.objects.filter(id__gt=nid,iCaption=detail_id).first()
            if next_obj:
                check = next_obj.iChecked
                next_obj_type=next_obj.iDevice
                macro_url = '\\' + str(next_obj.iurl[next_obj_type])
                next_caption_iname = next_obj.iname
                alex=next_obj.id
                pre_dict={'valid':True,'alex':alex,'macro_url':macro_url,'checkee':check,'iname':next_caption_iname}
                import json
                return HttpResponse(json.dumps(pre_dict))
            else:
                next_dict = {'valid': False, 'alex': None, 'macro_url': None}
                import json
                return HttpResponse(json.dumps(next_dict))
        elif flag=='download':
            import os, tempfile, zipfile
            from wsgiref.util import FileWrapper
            from django.utils.encoding import escape_uri_path
            origin_mark=req.POST.get('origin_mark')
            nid=req.POST.get('nid')
            caption=req.POST.get('download_caption')
            img_obj_download = models.imgUrl.objects.filter(iChecked=1,iCaption_id=nid)
            temp = tempfile.TemporaryFile()
            archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
            for foo in img_obj_download:
                obj_type=foo.iDevice
                if origin_mark:
                    filename = str(foo.iurl).replace('\\', '/')  # Select your files here.

                else:
                    filename = str(foo.iurl[obj_type])
                archive.write(filename,foo.iname)
            archive.close()
            data = temp.tell()
            temp.seek(0)
            wrapper = FileWrapper(temp)
            response = HttpResponse(wrapper, content_type='application/zip')
            last="attachment; filename*=utf-8''{}.zip".format(escape_uri_path(caption))
            response['Content-Disposition'] = last
            response['Content-Length'] = data
            return response
        elif flag=='origin':
            oid=req.POST.get('nid')
            img_Urlobj=models.imgUrl.objects.filter(id=oid).first()
            origin_path=img_Urlobj.iurl
            st_or=str(origin_path)
            st_or2='\\'+st_or
            print(type(st_or2))
            import json
            return HttpResponse(json.dumps(st_or2))
        elif flag=='download_all':
            import os, tempfile, zipfile
            from wsgiref.util import FileWrapper
            from django.utils.encoding import escape_uri_path
            origin_mark = req.POST.get('origin_mark2')
            nid=req.POST.get('nid')
            caption=req.POST.get('download_caption')
            img_obj_download = models.imgUrl.objects.filter(iCaption_id=nid)
            temp = tempfile.TemporaryFile()
            archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
            for foo in img_obj_download:
                obj_type = foo.iDevice
                if origin_mark:
                    filename = str(foo.iurl).replace('\\', '/')  # Select your files here.
                else:
                    filename = str(foo.iurl[obj_type])
                archive.write(filename, foo.iname)
            archive.close()
            data = temp.tell()
            temp.seek(0)
            wrapper = FileWrapper(temp)
            response = HttpResponse(wrapper, content_type='application/zip')
            last="attachment; filename*=utf-8''{}.zip".format(escape_uri_path(caption))
            response['Content-Disposition'] = last
            response['Content-Length'] = data
            return response
        elif flag=='name':
            img_id=req.POST.get('nid')
            import json
            caption_name=models.imgUrl.objects.filter(id=img_id).first()
            return HttpResponse(json.dumps(caption_name.iname))
        else:
            foo_id=req.POST.get('foo_id')
            foo_icaptionId=req.POST.get('foo_icaption')
            models.imgUrl.objects.filter(id=foo_id).delete()
            return redirect('/general_view.html/?nid=%s'%foo_icaptionId)
@method_decorator(auth,name='dispatch')
class upload(views.View):
    def get(self,req,*args,**kwargs):
        classes_obj = models.imgApartMent.objects.all()
        username = req.session.get('username')
        userid = req.session.get('id')
        user_permission = req.session.get('permission')
        return render(req,'upload.html',{'username': username,'classes_obj': classes_obj})
    def post(self,req,*args,**kwargs):
        img_caption = req.POST.get('caption')
        author=req.POST.get('author')
        keyword=req.POST.get('keyword')
        exist=models.imgDetail.objects.filter(caption=img_caption).count()
        classes_obj = models.imgApartMent.objects.all()
        username = req.session.get('username')
        userid = req.session.get('id')
        user_permission = req.session.get('permission')
        warnig='标题已存在'
        if exist:
            return render(req, 'upload.html', {'username': username, 'classes_obj': classes_obj,'warning':warnig})
        img_dates=req.POST.get('tims')
        img_dates=str(img_dates)
        import re
        mat = re.search(r"(\d{4}-\d{1,2}-\d{1,2})",img_dates)
        if not mat:
            date_warning='日期格式为xxxx-xx-xx例如：2018-01-01'
            return render(req, 'upload.html', {'username': username, 'classes_obj': classes_obj,'date_warning':date_warning})
        file=req.FILES.getlist('imgFile')
        img_caption=req.POST.get('caption')
        img_caption=str(img_caption)
        img_classes=req.POST.getlist('classes')

        img_classes=int(img_classes[0])
        import os
        img_apart=models.imgApartMent.objects.filter(id=img_classes).first().caption
        img_caption2 = str(img_dates) + "_" + str(img_caption)
        img_folder = os.path.join('static', 'upload', img_apart, img_caption2)
        try:
            detail_obj=models.imgDetail.objects.create(caption=img_caption,apartment_id=img_classes,idate=img_dates,folder=img_folder,author=author,keyword=keyword)
        except:
            return HttpResponse('上传失败')

        iCatpion_id=detail_obj.id
        img_caption=img_dates+"_"+img_caption
        import os
        create_path = os.path.join('static', 'upload', img_apart, img_caption)
        try:
            os.mkdir(create_path)
            for img_objs in file:
                from PIL import Image
                im = Image.open(img_objs)
                print('宽：%d,高：%d' % (im.size[0], im.size[1]))
                width = im.size[0]
                height = im.size[1]
                div_size = width / height
                if div_size == 0.75:
                    device='phone'
                else:
                    device='avatar'
                img_path = os.path.join(create_path, img_objs.name)
                f = open(img_path, 'wb')
                for fs in img_objs:
                    f.write(fs)
                img_url_obj = models.imgUrl.objects.create(iurl=img_path, iname=img_objs.name, iCaption=detail_obj,
                                                           idate=img_dates,iDevice=device)
            need_converObj=models.imgUrl.objects.filter(iCaption=iCatpion_id)

            for i in need_converObj:
                if i.iDevice == 'phone':
                    i.iurl['phone']
                    print('is a phone')
                else:
                    i.iurl['avatar']
            return redirect('/member.html/?nid=%d' % img_classes)
        except:
            return redirect('/upload.html')

@method_decorator(auth,name='dispatch')
class search(views.View):
    def get(self,req,*args,**kwargs):
        classes_obj = models.imgApartMent.objects.all()
        apart_id=req.GET.get('nid')
        username=req.session.get('username')
        userid=req.session.get('id')
        user_permission=req.session.get('permission')
        show_numer=15
        member_obj=models.imgDetail.objects.order_by('-idate')[0:show_numer]
        show_tittle="最新上传的%d条内容"%show_numer
        return render(req,'search.html',{'classes_obj':classes_obj,'username':username,'member_obj':member_obj,'user_permission':user_permission,'show_tittle':show_tittle})

    def post(self,req,*args,**kwargs):
        classes_obj = models.imgApartMent.objects.all()
        img_classes = req.POST.getlist('classes')
        img_classes = int(img_classes[0])
        keyword=req.POST.get('keyword')
        username = req.session.get('username')
        user_permission = req.session.get('permission')
        start_line=req.POST.get('start_line')
        dead_line=req.POST.get('dead_line')
        filter_obj=None
        import time
        if img_classes==10:
            if keyword:
                if start_line and dead_line:
                #     start_strip=time.mktime(time.strptime(start_line, '%Y-%m-%d'))
                #     dead_strip=time.mktime(time.strptime(dead_line, '%Y-%m-%d'))
                #     time_val=dead_strip-start_strip
                #     if time_val:
                    filter_obj = models.imgDetail.objects.filter(keyword__icontains=keyword,
                                                                     idate__range=[start_line, dead_line])
                else:
                    filter_obj = models.imgDetail.objects.filter(keyword__icontains=keyword)

            else:
                if start_line and dead_line:
                    # start_strip=time.mktime(time.strptime(start_line, '%Y-%m-%d'))
                    # dead_strip=time.mktime(time.strptime(dead_line, '%Y-%m-%d'))
                    # time_val=dead_strip-start_strip
                    # if time_val:
                    filter_obj = models.imgDetail.objects.filter(idate__range=[start_line, dead_line])
        else:
            if keyword:
                if start_line and dead_line:
                    # start_strip = time.mktime(time.strptime(start_line, '%Y-%m-%d'))
                    # dead_strip = time.mktime(time.strptime(dead_line, '%Y-%m-%d'))
                    # time_val = dead_strip - start_strip
                    # if time_val:
                    filter_obj = models.imgDetail.objects.filter(keyword__icontains=keyword,
                                                                     idate__range=[start_line, dead_line],apartment_id=img_classes)
                else:
                    filter_obj = models.imgDetail.objects.filter(keyword__icontains=keyword,apartment_id=img_classes)

            else:
                if start_line and dead_line:
                    # start_strip = time.mktime(time.strptime(start_line, '%Y-%m-%d'))
                    # dead_strip = time.mktime(time.strptime(dead_line, '%Y-%m-%d'))
                    # time_val = dead_strip - start_strip
                    # if time_val:
                    filter_obj = models.imgDetail.objects.filter(idate__range=[start_line, dead_line],apartment_id=img_classes)
        if filter_obj==None:
            filter_obj=models.imgDetail.objects.filter(apartment=img_classes)
        return render(req, 'search.html',
                      {'classes_obj':classes_obj,'username': username, 'member_obj': filter_obj, 'user_permission': user_permission,'show_tittle':'筛选结果'})
class download(views.View):
    def get(self, request, *args, **kwargs):
        return render(request, 'download.html')
    def post(self,request,*args, **kwargs):
        import os, tempfile, zipfile
        from django.http import HttpResponse
        from wsgiref.util import FileWrapper

        temp = tempfile.TemporaryFile()
        archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)

        filename = 'static/upload/IMG_0789.JPG'  # Select your files here.
        archive.write(filename)
        archive.close()
        data = temp.tell()
        temp.seek(0)
        wrapper = FileWrapper(temp)
        response = HttpResponse(wrapper, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=test.zip'
        response['Content-Length'] = data
        return response

