#!/usr/bin/env python3
"""Genera documento_presentacion_control.tex: cada lámina con su explicación y su guion, el cronograma,
el gemelo digital en detalle y la guía de la demostración.

    python3 hacer_deck.py          # presentación (.pptx) y datos_laminas.json
    (exportar el PDF de Google Slides y convertirlo: pdftoppm -r 110 -png presentacion.pdf laminas/l)
    python3 hacer_documento.py     # .tex; se compila con desarrollo/compilar_documentos.py
"""
import json
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(AQUI, 'datos_laminas.json'), encoding='utf-8'))

UNI = {'θ': r'$\theta$', 'τ': r'$\tau$', 'ρ': r'$\rho$', 'µ': r'$\mu$', 'Θ': r'$\Theta$', '·': r'$\cdot$',
       '→': r'$\rightarrow$', '↔': r'$\leftrightarrow$', '≈': r'$\approx$', '≤': r'$\le$', '−': '-', '–': '--',
       '—': '---', '«': r'\guillemotleft{}', '»': r'\guillemotright{}', '²': r'$^2$', '⁻': r'$^{-}$', '⁵': r'$^5$',
       '₀': r'$_0$', '₁': r'$_1$', 'ᵀ': r'$^T$', 'ẋ': r'$\dot x$', '↺': r'$\circlearrowleft$', '°': r'$^\circ$'}


def tex(s):
    s = s.replace('\\', r'\textbackslash{}')
    for a, b in (('&', r'\&'), ('%', r'\%'), ('#', r'\#'), ('_', r'\_'), ('$', r'\$'), ('{', r'\{'), ('}', r'\}'),
                 ('~', r'\textasciitilde{}'), ('^', r'\^{}')):
        s = s.replace(a, b)
    s = re.sub(r'"([^"]*)"', r'``\1' + "''", s)
    return ''.join(UNI.get(c, c) for c in s)


def mmss(s):
    return f'{s // 60}:{s % 60:02d}'


t = 0
filas, laminas = [], []
for l in D['laminas']:
    ini, fin = t, t + l['segundos']; t = fin
    filas.append(f"{l['n']:02d} & {tex(l['titulo'])} & {mmss(ini)}--{mmss(fin)} & {l['segundos']} s\\\\")
    laminas.append(rf"""
\section*{{Lámina {l['n']:02d} · {tex(l['titulo'])}}}
\addcontentsline{{toc}}{{subsection}}{{Lámina {l['n']:02d} · {tex(l['titulo'])}}}
\begin{{center}}\includegraphics[width=\linewidth]{{laminas/l-{l['n']:02d}.png}}\end{{center}}
\noindent\textbf{{Qué muestra.}} {tex(l['explicacion'])}

\begin{{guion}}{{{mmss(ini)} -- {mmss(fin)} \quad ({l['segundos']} s)}}
{tex(l['guion'])}
\end{{guion}}
\clearpage""")

PLANTILLA = r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish,es-noshorthands]{babel}
\usepackage{lmodern,microtype,graphicx,booktabs,tabularx,xcolor,amsmath,amssymb,float}
\usepackage[margin=2.2cm]{geometry}
\usepackage[most]{tcolorbox}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\definecolor{navy}{HTML}{12263A}\definecolor{teal}{HTML}{0F766E}\definecolor{nar}{HTML}{E8772E}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small\color{teal} Control y gemelo digital del brazo XK-JS1-1}
\fancyhead[R]{\small\color{teal} Presentación del 28/11/2026}
\fancyfoot[C]{\small\thepage}
\renewcommand{\headrulewidth}{0.4pt}
\setlength{\parindent}{0pt}\setlength{\parskip}{6pt}
\newtcolorbox{guion}[1]{enhanced,breakable,colback=teal!6,colframe=teal,boxrule=0.8pt,arc=2pt,
  title={\textbf{Guion} \hfill #1},fonttitle=\small\bfseries,coltitle=white,colbacktitle=teal}
\newtcolorbox{nota}{enhanced,breakable,colback=nar!8,colframe=nar,boxrule=0.8pt,arc=2pt}
\newcommand{\codigo}[1]{\texttt{#1}}
\begin{document}

\begin{titlepage}
\centering
{\large\color{navy} UNIVERSIDAD MAYOR DE SAN ANDRÉS\\ FACULTAD DE INGENIERÍA · INGENIERÍA ELECTRÓNICA\par}
\vspace{1.6cm}
{\color{nar}\bfseries MUESTRA DEL TRABAJO · MENCIÓN CONTROL\par}
\vspace{0.4cm}
{\Huge\bfseries\color{navy} Control y gemelo digital\\[4pt] del brazo robótico XK-JS1-1\\[4pt] de 4 grados de libertad\par}
\vspace{0.6cm}
{\Large Documento de la presentación: diapositivas, explicación y guion\par}
\vspace{1cm}
\includegraphics[width=0.75\linewidth]{laminas/l-01.png}\par
\vspace{1cm}
{\large Sistemas de Control II ETN-902 · Técnicas de Control ETN-1034\par}
\vspace{0.6cm}
Gabriel Andres Gomez Calla · Jose Lenin Mamani Choque\\
Miguel Alejandro Lima Huarachi · Román Abner Machicado Arequipa\\
Marco Eduardo Chura Rondo\par
\vfill
{\bfseries Escuadra 4GDL · La Paz, 28 de noviembre de 2026\par}
\end{titlepage}

\tableofcontents
\clearpage

\section{Cómo usar este documento}
Este documento acompaña a la presentación de unos 15 minutos sobre el trabajo realizado en el brazo XK-JS1-1,
con el enfoque de la mención de control. Para cada diapositiva se incluye la imagen, una explicación de lo que
muestra (para estudiar el contenido) y un \textbf{guion} con lo que se dice y el tiempo que le corresponde. El
mismo guion está en las notas del orador de la presentación de Google Slides y del archivo PowerPoint.

Después de las diapositivas hay dos capítulos de apoyo: el gemelo digital en detalle (para responder preguntas)
y la guía paso a paso de la demostración, con la habilitación de los observadores libres.

\begin{center}\small
\begin{tabularx}{\linewidth}{c X c r}
\toprule
\textbf{N.º} & \textbf{Lámina} & \textbf{Tiempo} & \textbf{Duración}\\
\midrule
%%FILAS%%
\midrule
 & \textbf{Total} & & \textbf{%%TOTAL%%}\\
\bottomrule
\end{tabularx}
\end{center}

\begin{nota}
\textbf{Reparto sugerido del tiempo.} Introducción (láminas 1--2): 1:15 · planta e instrumentación (láminas 3--5): 2:20 · estructura de control y
modelo (6--8, 11): 3:15 · diseño de controladores (9--10): 1:45 · gemelo digital (12--15): 3:20 ·
demostración (16): 2:00 · cierre (17--18): 0:55. Si el tiempo apremia, las láminas 5 y 11 se pueden pasar
en 15~s cada una; la demostración no se debe recortar.
\end{nota}
\clearpage

\section{Las diapositivas, explicadas}
%%LAMINAS%%

\section{El gemelo digital en detalle}
\subsection{Qué es}
Un gemelo digital es una réplica virtual de un sistema físico que se mantiene sincronizada con él: recibe
continuamente los datos de la planta, los representa con un modelo y puede devolverle órdenes. En este proyecto
el gemelo es una aplicación propia en Python, que corre en Linux y Windows sin internet, y una interfaz web con
el modelo 3D del brazo (three.js) construido con la cinemática y las cotas del modelo de Inventor del equipo.
Se eligió una aplicación propia en lugar de Simulink porque, además de simular, debía conectarse al PLC real y
servir de interfaz de operación.

\subsection{Partes de la aplicación}
\begin{center}\small
\begin{tabularx}{\linewidth}{>{\raggedright}p{4.2cm} X}
\toprule
\textbf{Parte} & \textbf{Función}\\
\midrule
Cliente PPI (\codigo{ppi.py}, \codigo{serie.py}) & habla con el PLC S7-200 por su puerto 0 (RS-485) con el cable USB-PPI, a 9,6~kbit/s; lee y escribe la memoria V, las entradas y las salidas\\
Brazo (\codigo{brazo.py}) & reconoce el programa cargado en el PLC (perfil), calcula la posición, valida las órdenes y maneja el mando exclusivo\\
Estimador & con el programa original del PLC, que no cuenta pulsos, estima la posición integrando la frecuencia de los trenes ($f\cdot dt$) y la corrige en los finales de carrera; error máximo 1,35~mm\\
PLC simulado & reproduce el programa \codigo{brazo\_gemelo} (pasos, tiempos y códigos de error) para usar todo sin hardware\\
Servidor (\codigo{gemelo\_brazo.py}) & sirve la interfaz en esta PC (\codigo{localhost:8050}) y, en el modo red, por HTTPS en el puerto 8443; usuarios, roles y observadores libres (\codigo{acceso.py})\\
Telemetría (\codigo{telemetria.py}) & CSV por sesión y PostgreSQL: 1 muestra/s por variable, señales, alarmas, órdenes e ingresos\\
API y Modbus (\codigo{api\_erp.py}, \codigo{modbus.py}) & API REST \codigo{/api/v1} con token y pasarela Modbus TCP de solo lectura (registros 40001--40015)\\
Interfaz (\codigo{ui/}) & modelo 3D, paneles Articular, Cartesiano, Secuencias y Conexión, y el dashboard\\
\bottomrule
\end{tabularx}
\end{center}

\subsection{Interfaz con el PLC (programa \codigo{brazo\_gemelo})}
La PC y el PLC se comunican por un bloque de memoria V. La PC escribe la orden y el PLC devuelve su estado:
\begin{center}\small
\begin{tabular}{l l l}
\toprule
\textbf{Dirección} & \textbf{Quién escribe} & \textbf{Contenido}\\
\midrule
VB1100 & PC & orden: 1 homing, 2 mover, 3 paro, 4 cerrar garra, 5 abrir garra\\
VB1101 & PC & secuencia (aumenta en 1 con cada orden)\\
VW1102 & PC & latido: si deja de cambiar, el watchdog del PLC detiene el brazo\\
VD1104 / VD1108 / VD1112 & PC & destino de la base, X e Y en pulsos (con signo)\\
VB1120 & PLC & estado: 0 reposo, 1 homing, 2 moviendo\\
VB1122 & PLC & banderas: referenciado, remoto, PTO ocupados, posición incierta, watchdog\\
VB1123 & PLC & error: ocupado, fuera de rango, watchdog, sin referencia, paro\\
VD1124 / VD1128 / VD1132 & PLC & posición de la base, X e Y en pulsos\\
VB1138--VB1140 & PLC & copia de IB0, IB1 y QB0; VB1141 = firma 16\#47 del programa\\
\bottomrule
\end{tabular}
\end{center}

\subsection{El ciclo de funcionamiento}
\begin{enumerate}
\item \textbf{Leer.} La app lee del PLC las entradas, las salidas y la memoria de estado. Cada lectura por PPI tarda unos 155~ms; ese es el periodo de supervisión.
\item \textbf{Calcular.} Con \codigo{brazo\_gemelo} la posición es la cuenta de pulsos del PLC, exacta mientras el motor no pierda pasos. Con el programa original, la estima el estimador.
\item \textbf{Mostrar.} La cinemática directa convierte $(\theta, s_X, s_Y)$ en la pose del brazo y el modelo 3D se mueve; se muestran las señales, alarmas y la telemetría.
\item \textbf{Mandar.} Una orden del operador se valida (rol, mando, homing hecho, límites) y se escribe en VB1100 con su secuencia; el PLC la ejecuta y corta los trenes en los finales de carrera.
\end{enumerate}

\subsection{Modos y seguridad}
\begin{itemize}
\item \textbf{Simulación}: PLC simulado; no necesita brazo ni cable.
\item \textbf{Operación local}: sigue al brazo real y lo manda desde la PC del laboratorio; nadie más se conecta.
\item \textbf{Operación por red local}: además, otras PC y celulares de la misma red entran por HTTPS. Roles: operador (ve y manda; uno solo tiene el mando a la vez), observador (solo ve) y observador libre (sin contraseña, solo ve).
\item El paro está siempre disponible; el watchdog del PLC detiene el brazo si la PC deja de comunicarse; la seta de emergencia física manda sobre todo. Las contraseñas se guardan con PBKDF2-SHA256 y sal; tras 5 intentos fallidos una dirección espera 60~s.
\end{itemize}

\subsection{Observadores libres}
Es la novedad de esta versión, pensada para clases y demostraciones con público:
\begin{itemize}
\item Se activa en el menú, en la tarjeta «Operación por red local», con la casilla \textbf{«Observadores libres: entrar sin contraseña, solo para ver»} (o al abrir la app con la opción \codigo{--observadores-libres}). Viene apagada cada vez que se abre la app.
\item Con la casilla marcada, el código QR del menú apunta a \codigo{https://IP:8443/libre}: quien lo escanea entra directo al gemelo como \codigo{visita-1}, \codigo{visita-2}, etc. En la pantalla de ingreso aparece además el botón «Entrar como observador (sin contraseña)».
\item Una visita ve el brazo en vivo y el dashboard, pero el servidor rechaza (código 403) cualquier orden o pedido de mando, y lo anota en el registro.
\item Al desmarcar la casilla, todas las sesiones de visitas se cierran al instante y el enlace \codigo{/libre} deja de funcionar.
\item Para mandar el brazo sigue haciendo falta un usuario operador con contraseña. Con observadores libres activos, la operación por red se puede abrir aunque todavía no haya usuarios creados.
\end{itemize}
Prueba realizada el 28/11/2026 con el PLC simulado: ingreso libre como \codigo{visita-1} (303 al gemelo),
lectura de estado (200), orden de homing y pedido de mando rechazados (403), y tras desactivar la opción la
sesión deja de valer (401) y \codigo{/libre} responde 403.

\clearpage
\section{Guía de la demostración}
\subsection{Antes de la presentación}
\begin{enumerate}
\item Conectar la PC a la red Wi-Fi del laboratorio (la misma que usarán los celulares del público).
\item Si se usará el brazo real: cable USB-PPI al puerto 0 del PLC, selector en remoto (I0.5), tablero energizado y una persona junto a la seta de emergencia. En Linux, si la máquina virtual de Windows XP está abierta, el USB del cable debe estar desmarcado en su menú Dispositivos.
\item Abrir la app: en Linux, menú de aplicaciones $\rightarrow$ \emph{Gemelo digital del brazo} (o \codigo{./iniciar\_gemelo.sh} en la carpeta de la app); en Windows, doble clic en \codigo{Gemelo digital.bat}.
\item Comprobar en el menú, recuadro «Estado», que se detecta el cable (Puertos) o, si no hay brazo, que se usará la casilla «Sin brazo».
\end{enumerate}

\subsection{Durante la demostración (unos 2 minutos)}
\begin{enumerate}
\item \textbf{Simulación (40 s).} Menú $\rightarrow$ Simulación $\rightarrow$ «Abrir». Pulsar «Homing»; en «Articular» mover la base y los carros; en «Cartesiano» elegir un punto (la app propone el alcanzable más cercano); botón «Espacio de trabajo».
\item \textbf{Red y observadores libres (20 s).} Botón «Menú» $\rightarrow$ tarjeta «Operación por red local»: marcar «Sin brazo» si no hay planta, marcar \textbf{«Observadores libres»} y pulsar «Abrir». Volver al menú para ver el QR («Brazo en la red local»).
\item \textbf{Público con el celular (40 s).} Pedir que escaneen el QR. La primera vez el navegador avisa del certificado propio: «Avanzado» $\rightarrow$ «Continuar». Cada uno entra como \codigo{visita-N} y ve el brazo moverse cuando el operador lo mueve desde la PC. Si alguien intenta mandar, aparece el aviso de solo lectura.
\item \textbf{Supervisión (20 s).} Botón «Dashboard»: indicadores y series de tiempo del movimiento recién hecho.
\item Al terminar, desmarcar «Observadores libres» para cerrar las sesiones de las visitas.
\end{enumerate}

\begin{nota}
\textbf{Plan B.} Si el brazo o el cable fallan, todo se puede mostrar con el PLC simulado (casilla «Sin brazo»).
Si los celulares no se conectan (red con aislamiento de clientes), se muestra el ingreso libre desde otra PC o
desde el navegador de la misma PC con la dirección que aparece bajo el QR.
\end{nota}

\subsection{Preguntas probables}
\begin{description}
\item[¿Por qué no hay control en lazo cerrado?] Porque no hay sensor continuo de posición: los finales de carrera y el inductivo son binarios. Sin medir la salida no hay error $e(k)$ que realimentar; la planta no es observable en continuo.
\item[¿Por qué el modelo es un integrador y no un primer orden?] El motor paso a paso con su driver convierte frecuencia en velocidad: la posición es la integral de la frecuencia. La dinámica del conjunto motor--carro, si existe, es de milisegundos y no se puede medir sin un sensor continuo.
\item[¿Qué impide el LQR?] Los carros X e Y comparten el tren de pulsos Q0.1: $B$ tiene rango 2 y el modo $s_X - s_Y$ no es controlable (queda un polo en $z=1$). Con un segundo tren de pulsos sí hay LQR de tres ejes.
\item[¿Qué tan fiel es el gemelo?] Con el programa \codigo{brazo\_gemelo} la posición es exacta al pulso mientras el motor no pierda pasos; con el programa original el estimador tiene un error máximo de 1,35~mm en 170~mm (99,2~\%). Falta la medición independiente con calibre.
\item[¿Es seguro dejar entrar a cualquiera?] El observador libre solo puede ver: el servidor valida el rol en cada petición y rechaza las órdenes; la opción viene apagada y se cierra al desmarcarla. El mando real requiere un operador con contraseña y la seta de emergencia sigue mandando sobre todo.
\item[¿Qué periodo de muestreo usarían?] 25~ms para un lazo en la interrupción temporizada del PLC (SMB34, evento 10) y unos 155~ms para supervisión desde la PC, que es lo que tarda una lectura PPI.
\end{description}

\end{document}
"""
salida = PLANTILLA.replace('%%FILAS%%', '\n'.join(filas)).replace('%%TOTAL%%', mmss(D['total_s'])) \
                  .replace('%%LAMINAS%%', '\n'.join(laminas))
open(os.path.join(AQUI, 'documento_presentacion_control.tex'), 'w', encoding='utf-8').write(salida)
print('documento_presentacion_control.tex', len(D['laminas']), 'láminas', mmss(D['total_s']))
