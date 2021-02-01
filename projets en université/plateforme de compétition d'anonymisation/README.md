## Installation:

### En utilisant docker-compose
#### Production: gunicorn + nginx
Construire les images:
```bash
docker-compose build
```
Exécuter les containers:
```bash
docker-compose up -d
```
Collecter les fichiers statiques pour la page admin:
```bash
docker-compose exec web python manage.py collectstatic --no-input --clear
```
Créer un nouveau super-utilisateur
```bash
docker-compose exec web python manage.py createsuperuser
```
Vérifier les erreurs dans les journaux
```bash
docker-compose logs -f
```
Le serveur est disponible sur [http://localhost:80]() \
Entrer dans l'environnement de la machine virtuel docker
```bash
docker-compose exec web sh
```
Faire arrêter les conteneurs:
```bash
docker-compose down -v
```


## Auteurs
* **Van Tuan Bui**
* **Armelle Nare**
* **Aziza Ezzaroualy**
* **Younes Baaomar**
* **Xavier Mendes**