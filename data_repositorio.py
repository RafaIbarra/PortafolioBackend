from typing import List,Union,Dict,  Set, Any
import requests
import re
import base64
import os
from collections import defaultdict
def fetch_auto_detected_frameworks():
    try:
        # 1. Obtener repositorios del usuario
        headers = {
            "Authorization": f"Bearer {os.getenv('VITE_GITHUB_TOKEN')}"
        }
        repos_response = requests.get(os.getenv('VITE_GITHUB_API_URL'), headers=headers)
        
        if not repos_response.ok:
            raise Exception("Error al obtener repositorios")
        
        repos = repos_response.json()

        # 2. Objeto para almacenar dependencias por repositorio
        repo_dependencies = {}

        # 3. Función auxiliar para detectar tipo de repositorio
        def detect_repo_type(repo):
            if repo.get('language') == 'Python':
                return 'python'
            if repo.get('language') in ('JavaScript', 'TypeScript'):
                return 'js'
            return 'other'

        # 4. Procesar cada repositorio
        for repo in repos:
            # Inicializar estructura para este repositorio
            repo_dependencies[repo['name']] = {
                'url': repo['html_url'],
                'packages': [],
                'has_dependencies': False,
                'type': detect_repo_type(repo)
            }

            # Consulta GraphQL para dependencias
            query = f"""
                query {{
                    repository(owner: "{repo['owner']['login']}", name: "{repo['name']}") {{
                        dependencyGraphManifests(first: 10) {{
                            nodes {{
                                filename
                                dependencies(first: 100) {{
                                    nodes {{
                                        packageName
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
            """

            try:
                graphql_response = requests.post(
                    "https://api.github.com/graphql",
                    headers={
                        "Authorization": f"Bearer {os.getenv('VITE_GITHUB_TOKEN')}",
                        "Content-Type": "application/json"
                    },
                    json={'query': query}
                )

                if not graphql_response.ok:
                    continue

                result = graphql_response.json()
                manifests = result.get('data', {}).get('repository', {}).get('dependencyGraphManifests', {}).get('nodes', [])

                # Procesar manifests encontrados
                for manifest in manifests:
                    if manifest['dependencies']['nodes']:
                        repo_dependencies[repo['name']]['has_dependencies'] = True
                        for dep in manifest['dependencies']['nodes']:
                            package_name = dep['packageName'].lower()
                            repo_dependencies[repo['name']]['packages'].append(package_name)

                # Fallback para Python (requirements.txt)
                if repo_dependencies[repo['name']]['type'] == 'python' and not repo_dependencies[repo['name']]['has_dependencies']:
                    try:
                        requirements_res = requests.get(
                            f"https://api.github.com/repos/{repo['owner']['login']}/{repo['name']}/contents/requirements.txt",
                            headers=headers
                        )
                        
                        if requirements_res.ok:
                            content = requirements_res.json()
                            text = base64.b64decode(content['content']).decode('utf-8')
                            packages = []
                            for line in text.split('\n'):
                                line = line.strip()
                                if line and not line.startswith('#'):
                                    package = line.split('=')[0].split('>')[0].split('<')[0].strip().lower()
                                    packages.append(package)
                            
                            repo_dependencies[repo['name']]['packages'].extend(packages)
                            repo_dependencies[repo['name']]['has_dependencies'] = len(packages) > 0
                    except Exception as e:
                        print(f"Error leyendo requirements.txt en {repo['name']}: {e}")

            except Exception as error:
                print(f"Error procesando {repo['name']}: {error}")

        # 5. Configuración de detección de frameworks con prioridades
        framework_detectors = {
            # JavaScript/React - Ordenados por prioridad (de mayor a menor)
            'react-native': {
                'name': 'React Native', 
                'pattern': re.compile(r'^(react\-native|@react\-native|@callstack|@react\-navigation)'),
                'priority': 2
            },
            'next': {
                'name': 'Next.js', 
                'pattern': re.compile(r'^next$'),
                'priority': 1
            },
            'react': {
                'name': 'React', 
                'pattern': re.compile(r'^react$'),
                'priority': 1
            },
            
            # Python - Ordenados por prioridad (de mayor a menor)
            'drf': {
                'name': 'Django REST Framework', 
                'pattern': re.compile(r'^(djangorestframework|drf\-|django\-rest\-)'),
                'priority': 2
            },
            'django': {
                'name': 'Django', 
                'pattern': re.compile(r'^django$'),
                'priority': 1
            },
            'fastapi': {
                'name': 'FastAPI', 
                'pattern': re.compile(r'(^|\/|-)fastapi(-|$)|^fast-api'),
                'priority': 1
            },
            
            # Otros frameworks
            'flask': {
                'name': 'Flask', 
                'pattern': re.compile(r'^flask$'),
                'priority': 1
            },
            'vue': {
                'name': 'Vue', 
                'pattern': re.compile(r'^vue'),
                'priority': 1
            },
            'angular': {
                'name': 'Angular', 
                'pattern': re.compile(r'^@angular'),
                'priority': 1
            }
        }

        ignore_patterns = [
            re.compile(r'^@babel'), re.compile(r'^eslint'), re.compile(r'^@types'), re.compile(r'^@vitejs'),
            re.compile(r'^lottie'), re.compile(r'^@ant'), re.compile(r'^@shopify'), re.compile(r'^@emotion'),
            re.compile(r'^hoist'), re.compile(r'^jest'), re.compile(r'^testing'), re.compile(r'^webpack'),
            re.compile(r'^babel'), re.compile(r'^@testing'), re.compile(r'^prettier'), re.compile(r'^stylelint')
        ]

        # 6. Procesamiento para framework_details
        framework_details = {}
        repo_to_framework = {}  # Diccionario para rastrear qué framework tiene cada repo

        for repo_name, repo_data in repo_dependencies.items():
            detected_frameworks = []

            for pkg in repo_data['packages']:
                if any(pattern.search(pkg) for pattern in ignore_patterns):
                    continue

                for key, detector in framework_detectors.items():
                    if detector['pattern'].search(pkg):
                        detected_frameworks.append({
                            'key': key,
                            'name': detector['name'],
                            'priority': detector.get('priority', 1)
                        })
                        break

            # Si se detectaron frameworks, seleccionar el de mayor prioridad
            if detected_frameworks:
                # Ordenar por prioridad descendente y luego por nombre para consistencia
                detected_frameworks.sort(key=lambda x: (-x['priority'], x['name']))
                selected_framework = detected_frameworks[0]
                
                # Registrar el framework seleccionado
                framework_name = selected_framework['name']
                
                if framework_name not in framework_details:
                    framework_details[framework_name] = {
                        'count': 0,
                        'repositories': []
                    }
                
                # Actualizar el registro del repositorio
                if repo_name in repo_to_framework:
                    # Si el repo ya estaba en otro framework, quitarlo
                    old_framework = repo_to_framework[repo_name]
                    if old_framework in framework_details:
                        framework_details[old_framework]['count'] -= 1
                        framework_details[old_framework]['repositories'] = [
                            r for r in framework_details[old_framework]['repositories'] 
                            if r['name'] != repo_name
                        ]
                
                # Añadir al nuevo framework
                repo_to_framework[repo_name] = framework_name
                framework_details[framework_name]['count'] += 1
                framework_details[framework_name]['repositories'].append({
                    'name': repo_name,
                    'url': repo_data['url'],
                    'type': repo_data['type']
                })

        
        return  framework_details
    

    except Exception as error:
        print("Error general:", error)
        raise error

def fetch_lenguajes():
    try:
        # 1. Obtener repositorios del usuario
        headers = {
            "Authorization": f"token {os.getenv('VITE_GITHUB_TOKEN')}"
        }
        repos_response = requests.get(os.getenv('VITE_GITHUB_API_URL'), headers=headers)
        
        if not repos_response.ok:
            raise Exception("Error al obtener repositorios")
        
        repos = repos_response.json()

        # 2. Objeto para almacenar total de bytes por lenguaje
        language_totals = defaultdict(int)

        # 3. Procesar cada repositorio para obtener lenguajes
        for repo in repos:
            try:
                languages_response = requests.get(repo['languages_url'], headers=headers)
                if languages_response.ok:
                    repo_languages = languages_response.json()
                    
                    # Sumar los bytes por lenguaje
                    for language, bytes_used in repo_languages.items():
                        language_totals[language] += bytes_used

            except Exception as e:
                print(f"Error obteniendo lenguajes para {repo['name']}: {e}")
                continue

        # 4. Calcular total de bytes
        total_bytes = sum(language_totals.values())

        # 5. Calcular porcentajes
        percentages = {}
        if total_bytes > 0:  # Evitar división por cero
            for language, bytes_used in language_totals.items():
                percentages[language] = (bytes_used / total_bytes * 100).__round__(2)
                

        # 6. Imprimir resultados
        print("Distribución de lenguajes:")
        for lang, percent in percentages.items():
            print(f"{lang}: {percent}")

        return percentages

    except Exception as error:
        print("Error general:", error)
        return {}