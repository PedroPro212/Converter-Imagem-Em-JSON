# GenSole – Conversor de Palmilhas (protótipo)

Aplicativo Windows/Linux em Python + Tkinter. Recebe uma imagem com silhueta escura em fundo claro, solicita o comprimento real em centímetros, preserva a proporção largura/comprimento e gera JSON com os campos do exemplo GenSole.

## Como executar

Instale Python 3.10 ou superior. Abra o terminal nesta pasta:

```powershell
py -m pip install -r requirements.txt
py app.py
```

No Linux, use `python3 -m pip install -r requirements.txt` e `python3 app.py` (Tkinter deve estar instalado).

## Passo a passo

1. Selecione uma imagem JPG/PNG da palmilha (silhueta escura sobre fundo claro, sem objetos ao redor).
2. Digite o comprimento real em centímetros (ex.: `27,0`).
3. Escolha um JSON de referência do GenSole ou mantenha o exemplo incluído.
4. Clique em **Atualizar prévia** para ver o contorno e a largura calculada.
5. Clique em **GERAR JSON** e escolha o destino.
6. Importe o JSON no GenSole e verifique se o contorno é mantido.

## Gerar executável Windows

```powershell
py -m pip install pyinstaller
py -m PyInstaller --noconfirm --onefile --windowed --name GenSole_Conversor --add-data "modelo_referencia.json;." --add-data "exemplo_palmilha.jpg;." app.py
```

O `.exe` estará em `dist/GenSole_Conversor.exe`.

## Limitações importantes

- É um **protótipo experimental**, não um conversor oficial ou validado pelo GenSole.
- O campo `calcContour` é exportado como `false` por padrão, para tentar evitar que o site refaça o contorno. O comportamento real do site ainda não foi confirmado.
- A largura é estimada pela proporção da silhueta na imagem. Se a foto estiver em perspectiva ou distorcida, a largura ficará incorreta.
- Campos geométricos do exemplo são escalados, mas a superfície 3D **não é reconstruída anatomicamente**. A exportação STL pode falhar ou resultar em uma forma diferente.
- O programa não realiza calibração médica, ortopédica ou de impressão em escala real.
