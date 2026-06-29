import os
import sys
import re
import subprocess
import urllib.request
import urllib.error

def issue_existe_no_github(repo, token, numero_issue):
    url = f"https://api.github.com/repos/{repo}/issues/{numero_issue}"
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'GitHub-Actions-Validator')
    req.add_header('Authorization', f'token {token}')
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                return True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        print(f"Erro na API do GitHub: HTTP {e.code}")
    except Exception as e:
        print(f"Erro de conexão: {e}")
    return False

def obter_mensagens_commits():
    branch_destino = os.environ.get("TARGET_BRANCH", "main")
    
    try:
        resultado = subprocess.run(
            ["git", "log", f"origin/{branch_destino}..HEAD", "--format=%s"],
            capture_output=True, text=True, check=True
        )
        return [linha.strip() for linha in resultado.stdout.split('\n') if linha.strip()]
    except Exception as e:
        resultado = subprocess.run(
            ["git", "log", "-1", "--format=%s"],
            capture_output=True, text=True, check=True
        )
        return [resultado.stdout.strip()]

def main():
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("REPO")
    
    mensagens = obter_mensagens_commits()
    print(f"Encontrado(s) {len(mensagens)} commit(s) para validar neste Pull Request.")
    
    sucesso_geral = True

    for msg in mensagens:
        print(f"\nAnalisando commit: '{msg}'")
        cmp = re.match(r"^#(\d+) -", msg)
        
        if cmp:
            numero_issue = cmp.group(1)
            print(f"-> Verificando se a issue #{numero_issue} existe em {repo}...")
            
            if issue_existe_no_github(repo, token, numero_issue):
                print("-> Código e Issue válidos!")
            else:
                print(f"-> ERRO: A issue #{numero_issue} NÃO existe no GitHub.")
                sucesso_geral = False
        else:
            print("-> ERRO: Mensagem fora do padrão! Deve começar com '#NUM - '")
            sucesso_geral = False

    if not sucesso_geral:
        print("\n[FALHA] Um ou mais commits não passaram na validação.")
        sys.exit(1) # Reprova o Workflow no GitHub
        
    print("\n[SUCESSO] Todos os commits estão válidos!")
    sys.exit(0)

if __name__ == "__main__":
    main()