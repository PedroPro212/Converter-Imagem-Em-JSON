"""Conversor de silhueta de palmilha para JSON experimental GenSole."""
import copy
import json
import math
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import cv2
import numpy as np
from PIL import Image, ImageTk

BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
REFERENCE_FILE = BASE / "modelo_referencia.json"

def extract_shape(path, count=100):
    """Retorna duas bordas de cima para baixo, em pixels, e dimensões da máscara."""
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError('Não foi possível abrir a imagem. Use JPG ou PNG.')
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Silhueta escura em fundo claro; ignora pequenos ruídos.
    _, binary = cv2.threshold(gray, 170, 255, cv2.THRESH_BINARY_INV)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(binary)
    if n <= 1:
        raise ValueError('Nenhuma silhueta escura encontrada.')
    largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    mask = np.uint8(labels == largest) * 255
    x, y, w, h = cv2.boundingRect(mask)
    area = int(np.count_nonzero(mask))
    if area < 100:
        raise ValueError('A silhueta detectada é muito pequena.')
    mask = mask[y:y+h, x:x+w]
    if w > h:
        mask = cv2.rotate(mask, cv2.ROTATE_90_CLOCKWISE)
    h, w = mask.shape
    # Suavização leve, preservando a proporção original.
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    ys = np.linspace(0, h-1, count)
    left, right = [], []
    for yy in ys:
        yi = int(round(yy))
        xs = np.flatnonzero(mask[yi] > 0)
        if not len(xs):
            for delta in range(1, h):
                for row in (yi-delta, yi+delta):
                    if 0 <= row < h:
                        xs = np.flatnonzero(mask[row] > 0)
                        if len(xs): break
                if len(xs): break
        left.append(float(xs[0])); right.append(float(xs[-1]))
    return np.array(left), np.array(right), ys, w, h

def normal_vectors(points, sign):
    arr = np.array([[p['x'], p['y']] for p in points], dtype=float)
    output = []
    for i in range(len(arr)):
        a = arr[max(0, i-1)]; b = arr[min(len(arr)-1, i+1)]
        dx, dy = b-a
        norm = math.hypot(dx, dy) or 1
        # Bordas orientadas do topo ao calcanhar; vetores externos.
        output.append({'x': round(sign*(-dy)/norm, 6), 'y': round(sign*dx/norm, 6)})
    return output

def create_model(reference, left, right, ys, pixel_width, pixel_height, length_mm, force_recalc=False):
    data = copy.deepcopy(reference)
    # Escala uniforme: comprimento fornecido pelo usuário; largura da imagem.
    scale = length_mm / max(pixel_height-1, 1)
    center = (np.max(right) + np.min(left)) / 2
    y_coords = (pixel_height-1-ys)*scale
    # Centro do contorno no eixo x, mantendo assimetria anatômica.
    in_pts = [{'x':round(float((x-center)*scale),5),'y':round(float(y),5)} for x,y in zip(right,y_coords)]
    out_pts = [{'x':round(float((x-center)*scale),5),'y':round(float(y),5)} for x,y in zip(left,y_coords)]
    width = float((np.max(right)-np.min(left))*scale)
    old_l = float(reference.get('l', 119.4556))
    old_w = float(reference.get('w', 68))
    sx, sy = width/max(old_w,1e-8), length_mm/max(old_l,1e-8)
    data['l'] = round(length_mm,5)
    data['w'] = round(width,5)
    for key in ('hr','tr','iw','ow','io','oo','ir','or','otr'):
        if isinstance(data.get(key),(float,int)):
            data[key] = round(data[key]*sx,5)
    for key in ('il','ol','archOffsetY'):
        if isinstance(data.get(key),(float,int)):
            data[key] = round(data[key]*sy,5)
    for key in ('ii1','ii2','ii3','oi1','oi2','oi3'):
        if isinstance(data.get(key),list) and len(data[key])==2:
            data[key]=[round(data[key][0]*sx,5),round(data[key][1]*sy,5)]
    # Atualiza coordenadas de superfícies preexistentes, sem afirmar que
    # isso reconstrói uma malha 3D anatômica válida.
    patch=data.get('upperSurfacePatch',{})
    for curve in patch.values():
        if isinstance(curve,dict):
            for v in curve.values():
                if isinstance(v,dict):
                    if 'x' in v: v['x']=round(v['x']*sx,5)
                    if 'y' in v: v['y']=round(v['y']*sy,5)
    for key in ('minThicknessPlantar','minThicknessHeel'):
        v=data.get(key)
        if isinstance(v,dict):
            if 'x' in v:v['x']=round(v['x']*sx,5)
            if 'y' in v:v['y']=round(v['y']*sy,5)
    data['inPoints']=in_pts
    data['outPoints']=out_pts
    data['inNormals']=normal_vectors(in_pts, 1)
    data['outNormals']=normal_vectors(out_pts, -1)
    data['calcContour']=bool(force_recalc)
    data['showDimensions']=True
    data['loaded']=True
    return data, width

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('GenSole | Conversor de Palmilhas')
        self.geometry('990x720')
        self.minsize(820,620)
        self.configure(bg='#101820')
        self.image_path=tk.StringVar()
        self.length=tk.StringVar(value='27,0')
        self.model=None
        self.shape=None
        self._preview_image=None
        self._ui()
    def _ui(self):
        style=ttk.Style(self);style.theme_use('clam')
        style.configure('TFrame',background='#101820')
        style.configure('TLabel',background='#101820',foreground='#e6eff5',font=('Segoe UI',10))
        style.configure('TButton',padding=8,font=('Segoe UI',10))
        style.configure('TEntry',padding=5)
        header=ttk.Frame(self);header.pack(fill='x',padx=22,pady=(18,8))
        ttk.Label(header,text='GENSOLE  /  CONVERSOR DE PALMILHAS',font=('Segoe UI',17,'bold')).pack(anchor='w')
        ttk.Label(header,text='Imagem de silhueta → contorno proporcional → JSON experimental',font=('Segoe UI',10)).pack(anchor='w',pady=(5,0))
        content=ttk.Frame(self);content.pack(fill='both',expand=True,padx=22,pady=12)
        left=ttk.Frame(content,width=385);left.pack(side='left',fill='y',padx=(0,22));left.pack_propagate(False)
        right=ttk.Frame(content);right.pack(side='left',fill='both',expand=True)
        ttk.Label(left,text='1. Imagem da palmilha',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(8,5))
        ttk.Entry(left,textvariable=self.image_path).pack(fill='x')
        ttk.Button(left,text='Selecionar imagem (PNG / JPG)',command=self.select_image).pack(fill='x',pady=(7,20))
        ttk.Label(left,text='2. Comprimento real (cm)',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(0,5))
        ttk.Entry(left,textvariable=self.length).pack(fill='x')
        self.length.trace_add('write',lambda *_: self._invalidate())
        ttk.Label(left,text='A largura será calculada pela proporção da imagem.').pack(anchor='w',pady=(6,20))
        ttk.Label(left,text='Modelo GenSole incorporado ao aplicativo.',wraplength=365).pack(anchor='w',pady=(0,20))
        ttk.Button(left,text='Atualizar prévia',command=self.preview).pack(fill='x',pady=4)
        ttk.Button(left,text='GERAR JSON',command=self.export).pack(fill='x',pady=(10,8))
        self.status=ttk.Label(left,text='Selecione uma imagem.',wraplength=365,justify='left')
        self.status.pack(fill='x',pady=(15,0))
        ttk.Label(right,text='PRÉ-VISUALIZAÇÃO DO CONTORNO',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(8,8))
        self.canvas=tk.Canvas(right,bg='#f7f7f7',highlightthickness=0)
        self.canvas.pack(fill='both',expand=True)
        self.canvas.bind('<Configure>',lambda e:self._draw())
        footer=ttk.Label(self,text='Importante: contorno 2D experimental. A malha 3D e a importação no GenSole precisam de validação.',wraplength=950)
        footer.pack(fill='x',padx=22,pady=(0,15))
    def select_image(self):
        p=filedialog.askopenfilename(filetypes=[('Imagens','*.png *.jpg *.jpeg *.bmp')]);
        if p:self.image_path.set(p);self.preview()
    def _invalidate(self):
        self.model = None
        self.status.config(text="Comprimento alterado. Atualize a prévia ou gere o JSON.")
        self._draw()

    def _build(self):
        p=Path(self.image_path.get())
        if not p.is_file():raise ValueError('Selecione uma imagem válida.')
        if not REFERENCE_FILE.is_file():raise ValueError('Modelo interno não encontrado. Reinstale o aplicativo.')
        try:
            length=float(self.length.get().strip().replace(',','.'))
        except ValueError:
            raise ValueError('Informe um comprimento numérico em centímetros.')
        if not math.isfinite(length) or not 5<=length<=50:raise ValueError('Informe comprimento entre 5 e 50 cm.')
        with REFERENCE_FILE.open(encoding='utf-8') as f: template=json.load(f)
        for key in ('inPoints','outPoints','upperSurfacePatch'):
            if key not in template:raise ValueError(f'O modelo de referência não possui {key}.')
        left,right,ys,w,h=extract_shape(p)
        data,width=create_model(template,left,right,ys,w,h,length*10,False)
        return data,width
    def preview(self):
        try:
            self.model,width=self._build()
            self.status.config(text=f'Contorno pronto: {self.model["l"]/10:.1f} cm de comprimento × {width/10:.1f} cm de largura.\n{len(self.model["inPoints"])} pontos por lateral.')
            self._draw()
        except Exception as e:
            self.model=None;self.status.config(text=f'Erro: {e}')
    def _draw(self):
        self.canvas.delete('all')
        if not self.model:return
        points=self.model['inPoints']+list(reversed(self.model['outPoints']))
        w=max(self.canvas.winfo_width(),100);h=max(self.canvas.winfo_height(),100)
        minx=min(p['x'] for p in points);maxx=max(p['x'] for p in points)
        miny=min(p['y'] for p in points);maxy=max(p['y'] for p in points)
        s=min((w-70)/max(maxx-minx,1),(h-70)/max(maxy-miny,1))
        coords=[]
        for p in points:
            coords.extend([(p['x']-(minx+maxx)/2)*s+w/2,h/2-(p['y']-(miny+maxy)/2)*s])
        self.canvas.create_polygon(coords,fill='#333538',outline='#88a936',width=2,smooth=False)
        self.canvas.create_text(w/2,h-18,text=f'{self.model["l"]/10:.1f} cm × {self.model["w"]/10:.1f} cm (proporção estimada)',fill='#333538',font=('Segoe UI',10))
    def export(self):
        try:
            self.preview()
            if self.model is None:
                messagebox.showerror('Erro', self.status.cget('text'))
                return
            target=filedialog.asksaveasfilename(title='Salvar JSON GenSole',defaultextension='.json',initialfile='Palmilha_GenSole.json',filetypes=[('JSON','*.json')])
            if not target:return
            with open(target,'w',encoding='utf-8') as f:json.dump(self.model,f,indent=2,ensure_ascii=False)
            messagebox.showinfo('JSON criado',f'Arquivo salvo em:\n{target}\n\nTeste a importação no GenSole. O modelo 3D ainda não está validado.')
        except Exception as e:messagebox.showerror('Erro',str(e))

if __name__=='__main__':App().mainloop()
