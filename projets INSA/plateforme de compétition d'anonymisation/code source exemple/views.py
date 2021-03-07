from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.urls import reverse_lazy

# from django.db.models.functions import Greatest
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)
from .models import Soumission, Competition
from .models import A_soumission
from soumission import forms
import operator
from django.urls import reverse_lazy, reverse
from django.contrib.staticfiles.views import serve
from django.core.files.base import ContentFile
from django.core.files import File

import threading
from zipfile import ZipFile, ZIP_DEFLATED
import io
from django.db.models import Q
from pathlib import Path
from .Utility.grid import *
from .Utility.export import *
from .Utility.score_attack import *


from importlib import util

def load_file_as_module(name, location):
    spec = util.spec_from_file_location(name, location)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def home(request):
    context = {
        'competitions': Competition.objects.all()
    }
    return render(request, 'competition/home.html', context)


def search(request):
    template='soumission/home.html'
    query=request.GET.get('q')
    result=Soumission.objects.filter(Q(title__icontains=query) | Q(author__username__icontains=query) | Q(content__icontains=query))
    paginate_by=2
    context={ 'soumissions':result }
    return render(request,template,context)


def classement(request, pk=None):
    template='soumission/classement.html'
    c = Competition.objects.get(id=pk)
    soumissions = Soumission.objects.filter(competition=c, is_public=True).exclude(score_utility__isnull=True).order_by('-final_score')
    a_soumissions = A_soumission.objects.filter(competition=c).order_by('score_attack')
    known_authors = []
    team_ranking={}
    classement_global = []
    classement_a_global =[]
    classement_tcl = []
    classement_ifl = []
    classement_cvl = []
    classement_a_tcl = []
    classement_a_ifl = []
    classement_a_cvl = []
    members_of_tcl=[]
    members_of_ifl=[]
    members_of_cvl=[]
    
    final_score_attack = []

    for s in soumissions :
        classement_global.append(s)

    for i in soumissions:
        if i.author not in known_authors:
            known_authors.append(i.author)
    
    for a in a_soumissions:
        if a.author not in known_authors:
            known_authors.append(a.author)
    
    final_score_attack = [[[] for d in known_authors] for a in known_authors]
    
    for a in range(len(known_authors)):
        attacker = known_authors[a]
        print("Attacker: ", attacker)
        for defender in [u for u in known_authors if u != attacker]:
            print("Défender: ", defender)
            defender_soumissions = Soumission.objects.filter(competition=c, author=defender, is_public=True).exclude(score_utility__isnull=True)
            
            for s in defender_soumissions:
                attacker_A_d = A_soumission.objects.filter(author=attacker, competition=c, soumission=s).order_by('-score_attack')
                best_a_attack = 0
                for a_s in attacker_A_d:
                    best_a_attack = a_s.score_attack
                    # final_score_attack[attacker][defender].append(a_s) 
                    break
                print(known_authors.index(defender))
                print("Best attack: ", best_a_attack)
                final_score_attack[a][known_authors.index(defender)].append(best_a_attack) 
    
    
    for a in range(len(known_authors)):
        attacker = known_authors[a]
        team_ranking[attacker] = 0
        for defender in [u for u in known_authors if u != attacker]:
            d = known_authors.index(defender)
            defender_soumissions = Soumission.objects.filter(competition=c, author=defender, is_public=True).exclude(score_utility__isnull=True)
            
            if defender_soumissions.count() != len(final_score_attack[a][d]) or len(final_score_attack[a][d]) == 0:
                team_ranking[attacker] += 0
            else:
                team_ranking[attacker] += min(final_score_attack[a][d])
            
                for s in defender_soumissions:
                    attacker_A_d = A_soumission.objects.filter(author=attacker, competition=c, soumission=s).order_by('score_attack')
                    
                    for a_s in attacker_A_d:
                        if a_s.score_attack == min(final_score_attack[a][d]):
                            classement_a_global.append(a_s)
                            break
            
    
    # for k in known_authors:
    #     worst_attack=A_soumission.objects.filter(author=k, competition=c).order_by('score_attack')
    #     team_attacked=[]
    #     for w_a in worst_attack:
    #         if w_a.soumission.author not in team_attacked:
    #             team_attacked.append(w_a.soumission.author)
    #             classement_a_global.append(w_a)

    # for k in known_authors:
    #     team_final_a_score=0
    #     for t in classement_a_global:
    #         if t.author == k:
    #             team_final_a_score+=t.score_attack
    #     team_ranking[k]=team_final_a_score


    for el in classement_a_global:
        if (el.author.profile.choice == "TC INSA LYON"):
            classement_a_tcl.append(el)
            members_of_tcl.append(el.author)
        elif (el.author.profile.choice == "IF INSA LYON"):
            classement_a_ifl.append(el)
            members_of_ifl.append(el.author)
        else:
            classement_a_cvl.append(el)
            members_of_cvl.append(el.author)

    team_a_ranking=dict(sorted(team_ranking.items(), key=operator.itemgetter(1), reverse=True))
    members_of_tcl = list(set(members_of_tcl))
    members_of_ifl = list(set(members_of_ifl))
    members_of_cvl = list(set(members_of_cvl))

    d_soumissions = Soumission.objects.filter(competition=c, is_public=True).exclude(score_utility__isnull=True)

    for e in d_soumissions:
        if(e.author.profile.choice == "TC INSA LYON"):
            best_attack = A_soumission.objects.filter(soumission=e, competition=c).order_by('-score_attack')
            best_a_attack = 0
            for a_s in best_attack:
                if a_s.author.profile.choice == "TC INSA LYON":
                    best_a_attack = a_s.score_attack
                    break

            e.final_score = e.score_utility * (1 - best_a_attack)
            classement_tcl.append(e)

        elif(e.author.profile.choice == "IF INSA LYON"):
            best_attack = A_soumission.objects.filter(soumission=e, competition=c).order_by('-score_attack')
            best_a_attack = 0
            for a_s in best_attack:
                if a_s.author.profile.choice == "IF INSA LYON":
                    best_a_attack = a_s.score_attack
                    break

            e.final_score = e.score_utility * (1 - best_a_attack)
            classement_ifl.append(e)

        elif(e.author.profile.choice == "STI INSA CVL"):
            best_attack = A_soumission.objects.filter(soumission=e, competition=c).order_by('-score_attack')
            best_a_attack = 0
            for a_s in best_attack:
                if a_s.author.profile.choice == "STI INSA CVL":
                    best_a_attack = a_s.score_attack
                    break

            e.final_score = e.score_utility * (1 - best_a_attack)
            classement_cvl.append(e)

    classement_tcl.sort(key=lambda x: x.final_score, reverse=True)
    classement_ifl.sort(key=lambda x: x.final_score, reverse=True)
    classement_cvl.sort(key=lambda x: x.final_score, reverse=True)
    context={ 'classement': classement_global, 'competition_id': pk, 'classement_tclyon':classement_tcl, 'classement_iflyon':classement_ifl, 'classement_sticvl': classement_cvl, 'classement_a':classement_a_global,'classement_a_tcl':classement_a_tcl,'classement_a_ifl':classement_a_ifl, 'classement_a_cvl':classement_a_cvl, 't_ranking': team_a_ranking, 'members_of_tcl': members_of_tcl, 'members_of_ifl': members_of_ifl, 'members_of_cvl': members_of_cvl }
    return render(request,template,context)



def getfile(request):
   return serve(request, 'File')


class CompetitionListView(ListView):
    model = Competition
    template_name = 'competition/home.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'competitions'
    ordering = ['-date_posted']
    paginate_by = 10
    

# =============================================================================
# class UserCompetitionListView(ListView):
#     model = Competition
#     template_name = 'soumission/user_competitions.html'  # <app>/<model>_<viewtype>.html
#     context_object_name = 'competitions'
#     paginate_by = 10
# 
#     def get_queryset(self):
#         user = get_object_or_404(User, username=self.kwargs.get('username'))
#         return Competition.objects.filter(author=user).order_by('-date_posted')
# =============================================================================
    

def decompress_gt(c_id):
    object_c = get_object_or_404(Competition, id=c_id)
    gt = object_c.ground_truth_file_zip
    
    # Create a ZipFile Object and load sample.zip in it
    with ZipFile(gt.path, 'r') as zipGt:
       # Get a list of all archived file names from the zip
       listOfFileNames = zipGt.namelist()
       # Iterate over the file names
       for fileName in listOfFileNames:
           # Check filename endswith csv
           if fileName.endswith('.csv'):
               # Extract a single file from zip
               zipGt.extract(fileName, tmp)
               s = open(os.path.join(tmp, fileName), 'r')
               object_c.ground_truth_file.save(fileName, File(s))
               # print("Ground truth: ", object_c.ground_truth_file.path)
               object_c.save()
               s.close()
               print("Ground truth: ", object_c.ground_truth_file.path)
               if os.path.isfile(os.path.join(tmp, fileName)):
                   os.remove(os.path.join(tmp, fileName))
               break
           

class CompetitionCreateView(LoginRequiredMixin, CreateView):
    model = Competition
    form_class = forms.NewCompetitionForm
    success_url = reverse_lazy('DARC-home')
    template_name = 'competition/competition_form.html'
    # fields = ['title', 'rule', 'start_date_anon', 'end_date_anon', 'start_date_deanon', 'end_date_deanon', 'ground_truth_file']

    def form_valid(self, form):
        form.instance.author = self.request.user
        self.object = form.save(commit=True)
        
        t = threading.Thread(target=decompress_gt, args=[self.object.id])
        t.setDaemon(True)
        t.start()
        
        self.object.start_date_anon = form.instance.start_date_anon
        self.object.end_date_anon = form.instance.end_date_anon
        self.object.start_date_deanon = form.instance.start_date_deanon
        self.object.end_date_deanon = form.instance.end_date_deanon
        # self.object.ground_truth_file = self.object.ground_truth_file_zip
        self.object.save()
        # print("Date: ", type(self.object.start_date_deanon))
        #form.save()
        return redirect(self.get_success_url())
        

class CompetitionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Competition
    form_class = forms.NewCompetitionForm
    template_name = 'competition/competition_form.html'
    # fields = ['title', 'rule', 'start_date_anon', 'end_date_anon', 'start_date_deanon', 'end_date_deanon', 'ground_truth_file', 'script_utility']

    def form_valid(self, form):
        # form.instance.author = self.request.user
        # super().form_valid(form)
        object_c = get_object_or_404(Competition, id=form.instance.id)
        
        # print("Self: ", object_c.ground_truth_file_zip.path)
        # print("Form: ", form.instance.ground_truth_file_zip.path)
        if object_c.ground_truth_file_zip.path != form.instance.ground_truth_file_zip.path: 
            object_c.ground_truth_file_zip = form.instance.ground_truth_file_zip
            object_c.save()
            print("Oui, un changement du gt")
            t = threading.Thread(target=decompress_gt, args=[form.instance.id])
            t.setDaemon(True)
            t.start()
            
        if object_c.script_utility.path != form.instance.script_utility.path:
            object_c.script_utility = form.instance.script_utility
            object_c.save()
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('DARC-home')

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return False
    
    
class CompetitionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Competition
    success_url = '/'
    template_name = 'soumission/competition_confirm_delete.html'

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return False
    
    
class SoumissionListView(ListView):
    model = Soumission
    template_name = 'soumission/home.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'soumissions'
    ordering = ['-date_posted']
    paginate_by = 10
    
    def get_queryset(self):
        competition = get_object_or_404(Competition, pk=self.kwargs.get('pk'))
        return Soumission.objects.filter(competition=competition, is_public=True).order_by('-date_posted')
    
    def get_context_data(self, **kwargs):
        """
        This has been overridden to add `Asoumissions` to the template context,
        now you can use {{ Asoumissions }} within the template
        """
        context = super().get_context_data(**kwargs)
        context['competition_id'] = self.kwargs.get('pk')
        # print(context['competition_id'])
        return context


class UserSoumissionListView(ListView):
    model = Soumission
    template_name = 'soumission/user_soumissions.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'soumissions'
    paginate_by = 10

    def get_queryset(self):
        competition = get_object_or_404(Competition, pk=self.kwargs.get('pk'))
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Soumission.objects.filter(author=user, competition=competition).order_by('-date_posted')
    
    def get_context_data(self, **kwargs):
        """
        This has been overridden to add `Asoumissions` to the template context,
        now you can use {{ Asoumissions }} within the template
        """
        context = super().get_context_data(**kwargs)
        context['competition_id'] = self.kwargs.get('pk')
        print(context['competition_id'])
        return context
    
    
class SoumissionDetailView(LoginRequiredMixin, DetailView):
    model = Soumission
    template_name = 'soumission/soumission_detail.html'
    
    def get_object(self):
        return get_object_or_404(Soumission, pk=self.kwargs.get('pks'))
    
    
    def get_context_data(self, **kwargs):
        """
        This has been overridden to add `Asoumissions` to the template context,
        now you can use {{ Asoumissions }} within the template
        """
        object_c = get_object_or_404(Competition, pk=self.kwargs.get('pkc'))
        context = super().get_context_data(**kwargs)
        print(self.object.id)
        context['Asoumissions'] = A_soumission.objects.filter(soumission=self.object, competition=object_c).order_by('date_posted')
        context['competition_id'] = self.kwargs.get('pkc')
        #print(context['competition_id'])
        if context['Asoumissions']:
            best_attack = A_soumission.objects.filter(soumission=self.object, competition=object_c).order_by('-score_attack')[0].score_attack
            if best_attack:
                self.object.final_score = self.object.score_utility * (1 - best_attack)
        else:
            self.object.final_score = self.object.score_utility
        self.object.save()
        return context


@login_required
def create_new_Asoumission(request, pkc=None, pks=None):
    Asoumission_form = forms.NewASoumissionForm(request.POST or None, request.FILES)
    
    if request.method == "POST":
        if Asoumission_form.is_valid():
            Asoumission = Asoumission_form.save(commit=False)
            Asoumission.soumission = Soumission.objects.get(id=pks)
            Asoumission.author = request.user
            Asoumission.competition = Competition.objects.get(id=pkc)
            Asoumission.save()
            
            try:
                Asoumission.score_attack = score_attack(Soumission.objects.get(id=pks).F_file.path, Asoumission.A_file.path)
                Asoumission.save()
                messages.success(request, 'A_Soumission a été créé avec succès')
            except:
                messages.error(request, "Erreur lors du calcul du score d'attaque")
                Asoumission.delete()
                # Asoumission.score_attack = 0
                # Asoumission.save()
                
            return redirect(reverse_lazy('soumission-detail', args=[pkc, pks]))
            
        else:
            for error in Asoumission_form.errors.values():
                messages.error(request, error)
    context = {
        "Asoumission": Asoumission_form,
        'competition_id': pkc
    }
    return render(request, 'soumission/A_soumission_form.html', context)
    
    
def is_soumission_valid(id_competition): 
    c = Competition.objects.filter(id=id_competition)[0]
    # print("Délai dans la soumission: ", c.start_date_anon)
    now = datetime.date.today()
    # print(c.start_date_anon <= now <= c.end_date_anon)
    if c.start_date_anon <= now <= c.end_date_anon:
        return True
    else:
        return False
    
    
def calcul_utility(s_id, ground_truth):
    # decompress_t.join()
    # Décompression du fichier soumission
    object_s = get_object_or_404(Soumission, id=s_id)
    soumission = object_s.file.path
    
    object_s.content = "En cours: Extrait du fichier soumission"
    object_s.save()
    try:
        # Create a ZipFile Object and load sample.zip in it
        with ZipFile(soumission, 'r') as zipS:
           # Get a list of all archived file names from the zip
           listOfFileNames = zipS.namelist()
           # Iterate over the file names
           for fileName in listOfFileNames:
               # Check filename endswith csv
               if fileName.endswith('.csv'):
                   # Extract a single file from zip
                   # _, f_name = os.path.split(fileName)
                   # f_name = os.path.splitext(f_name)[0]
                   zipS.extract(fileName, tmp)
                   print("File extrait: ", fileName)
                   # s = open(os.path.join(tmp, fileName), 'wb')
                   # s.write(zipS.read(fileName))
                   # s.close()
                   s = open(os.path.join(tmp, fileName), 'r')
                   object_s.file.save(fileName, File(s))
                   object_s.save()
                   s.close()
                   if os.path.isfile(os.path.join(tmp, fileName)):
                       os.remove(os.path.join(tmp, fileName))
                   break
    except:
          object_s.content = "Erreur lors de l'extrait du fichier soumission"
          object_s.save()
          return
      
    print("Finir extrait du fichier soumission")
    # from object_s.competition.script_utility.path import main
    utility = load_file_as_module('mymodule', object_s.competition.script_utility.path)
    # export = Utility(ground_truth, object_s.file.path)
    # scores.scores_utility()
    # object_s.score_utility = scores.final_utility()
    # object_s.final_score = object_s.score_utility
    
    print("Produit des fichiers S et F")
    object_s.content = "En cours: Produit du fichier S_soumission"
    object_s.save()
    try: 
    # print("File name: ", object_s.file.name)
        export_S_soumission(object_s.file.path)
        print("Terminer S")
    except:
        object_s.content = "Erreur lors du produit du fichier S_soumission"
        object_s.save()
        if os.path.isfile(os.path.join(tmp, 'S_soumission.csv')):
            os.remove(os.path.join(tmp, 'S_soumission.csv'))
        return
    
    object_s.content = "En cours: Produit du fichier F_soumission"
    object_s.save()
    
    try:
        r = export_F_soumission(ground_truth, object_s.file.path)
        if r == -1:
            object_s.content = "Erreur: Un id_user a deux id anonymisés différents pour la même semaine"
            object_s.save()
            return
    except:
        object_s.content = "Erreur lors du produit du fichier F_soumission"
        object_s.save()
        if os.path.isfile(os.path.join(tmp, 'F_soumission.csv')):
            os.remove(os.path.join(tmp, 'F_soumission.csv'))
        if os.path.isfile(os.path.join(tmp, 'S_soumission.csv')):
            os.remove(os.path.join(tmp, 'S_soumission.csv'))
        return
    
    print("Termine S et F")
    
    object_s.content = "En cours: Calcul du score d'utilité"
    object_s.save()
    
    try:
        object_s.score_utility = utility.main(ground_truth, object_s.file.path)
    except:
        object_s.content = "Erreur lors du calcul su score d'utilité"
        object_s.save()
        return
    
    print("Score d'utilité: ", object_s.score_utility)
    object_s.final_score = object_s.score_utility
    
    object_s.content = "En cours: Compression du fichier S_soumission"
    object_s.save()
    # Create a ZipFile Object
    with ZipFile(os.path.join(tmp, 'S_soumission.zip'), 'w') as zipF:
       # Add multiple files to the zip
       zipF.write(os.path.join(tmp, 'S_soumission.csv'), compress_type=ZIP_DEFLATED)
       zipF.close()
    
    print("Sauvegarder les fichiers S et F")
    s = open(os.path.join(tmp, 'S_soumission.zip'), 'rb')
    f = open(os.path.join(tmp, 'F_soumission.csv'), 'r')

    object_s.S_file.save('S_soumission.zip', ContentFile(s.read()))
    object_s.F_file.save('F_soumission.csv', File(f))
    object_s.content = ''
    object_s.save()
    s.close()
    f.close()
    if os.path.isfile(os.path.join(tmp, 'S_soumission.csv')):
        os.remove(os.path.join(tmp, 'S_soumission.csv'))
    if os.path.isfile(os.path.join(tmp, 'F_soumission.csv')):
        os.remove(os.path.join(tmp, 'F_soumission.csv'))
    if os.path.isfile(os.path.join(tmp, 'S_soumission.zip')):
        os.remove(os.path.join(tmp, 'S_soumission.zip'))
    
    

def decompress_soumission(s_id):
    object_s = get_object_or_404(Soumission, id=s_id)
    soumission = object_s.file
    
    # Create a ZipFile Object and load sample.zip in it
    with ZipFile(soumission.path, 'r') as zipS:
       # Get a list of all archived file names from the zip
       listOfFileNames = zipS.namelist()
       # Iterate over the file names
       for fileName in listOfFileNames:
           # Check filename endswith csv
           if fileName.endswith('.csv'):
               # Extract a single file from zip
               zipS.extract(fileName, SOMISSION_ZIP)
               s = open(os.path.join(SOMISSION_ZIP, fileName), 'r')
               object_s.file.save(fileName, File(s))
               object_s.save()
               break

    
class SoumissionCreateView(LoginRequiredMixin, CreateView):
    model = Soumission
    template_name = 'soumission/soumission_form.html'
    fields = ['title', 'file']

    def form_valid(self, form):
        is_soumission_valid(self.kwargs.get('pk'))
        competition = get_object_or_404(Competition, pk=self.kwargs.get('pk'))
        form.instance.author = self.request.user
        form.instance.competition = competition
        super().form_valid(form)
        
        # decompress_t = threading.Thread(target=decompress_soumission, args=[form.instance.id])
        # # decompress_t.setDaemon(True)
        # decompress_t.start()
        
        t = threading.Thread(target=calcul_utility, args=[form.instance.id, competition.ground_truth_file.path])
        t.setDaemon(True)
        t.start()
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('soumission-detail', kwargs={'pkc':self.kwargs.get('pk'), 'pks':self.object.id})
    
    def get_context_data(self, **kwargs):
        """
        This has been overridden to add `Asoumissions` to the template context,
        now you can use {{ Asoumissions }} within the template
        """
        context = super().get_context_data(**kwargs)
        context['competition_id'] = self.kwargs.get('pk')
        # print(context['competition_id'])
        return context


class SoumissionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Soumission
    template_name = 'soumission/soumission_form.html'
    fields = ['title']
    
    def get_object(self):
        return get_object_or_404(Soumission, pk=self.kwargs.get('pks'))
    
    def get_success_url(self):
        return reverse('soumission-detail', kwargs={'pkc':self.kwargs.get('pkc'), 'pks':self.kwargs.get('pks')})
    
    def form_valid(self, form):
        # form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        soumission = self.get_object()
        if self.request.user.is_superuser:
            return True
        return False
    
    def get_context_data(self, **kwargs):
        """
        This has been overridden to add `Asoumissions` to the template context,
        now you can use {{ Asoumissions }} within the template
        """
        context = super().get_context_data(**kwargs)
        context['competition_id'] = self.kwargs.get('pkc')
        # print(context['competition_id'])
        return context
    

class SoumissionPublishView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Soumission
    template_name = 'soumission/soumission_form.html'
    fields = ['is_public']
    
    def get_object(self):
        return get_object_or_404(Soumission, pk=self.kwargs.get('pks'))
    
    def get_success_url(self):
        return reverse('soumission-detail', kwargs={'pkc':self.kwargs.get('pkc'), 'pks':self.kwargs.get('pks')})
    
    def form_valid(self, form):
        # form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        soumission = self.get_object()
        if self.request.user == soumission.author and not soumission.is_public:
            return True
        return False
    
    def get_context_data(self, **kwargs):
        """
        This has been overridden to add `Asoumissions` to the template context,
        now you can use {{ Asoumissions }} within the template
        """
        context = super().get_context_data(**kwargs)
        context['competition_id'] = self.kwargs.get('pkc')
        # print(context['competition_id'])
        return context


class SoumissionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Soumission
    success_url = '/'
    template_name = 'soumission/soumission_confirm_delete.html'
    
    def get_object(self):
        return get_object_or_404(Soumission, pk=self.kwargs.get('pks'))
    
    def test_func(self):
        soumission = self.get_object()
        if self.request.user.is_superuser or (not soumission.is_public and self.request.user == soumission.author):
            return True
        return False
    
    def get_context_data(self, **kwargs):
        """
        This has been overridden to add `Asoumissions` to the template context,
        now you can use {{ Asoumissions }} within the template
        """
        context = super().get_context_data(**kwargs)
        context['competition_id'] = self.kwargs.get('pkc')
        print(context['competition_id'])
        return context


def about(request):
    return render(request, 'soumission/about.html', {'title': 'About'})
