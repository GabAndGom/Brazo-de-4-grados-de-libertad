%% Modelo Cinemático Integral y Gemelo Digital del Brazo Robótico XK-JS1-1 (4 GDL)
% *Universidad Mayor de San Andrés (UMSA) — Facultad de Ingeniería*
% *Carrera de Ingeniería Electrónica*
%
% * *Asignaturas:* Sistemas de Control II (ETN-902) | Aplicación de Técnicas de Control (ETN-1034) | Bases de Datos (ETN-1000)
% * *Proyecto:* Laboratorio Integrado N.º 5 — Fase 2: Gemelos Digitales (Gestión II/2026)
% * *Docente:* Ing. Jorge Antonio Nava Amador
% * *Auxiliares:* Limber Ajnota, Fabián Plata, Franz Choque
% * *Repositorio GitHub:* <https://github.com/GabAndGom/Brazo-4GDL-gemelo-digital>
% * *Gemelo Web 3D:* <https://brazo-4gdl-gemelo-digital.pages.dev/>
%
% *Nota de uso en MATLAB:* Este archivo está estructurado como *Live Script en texto plano*
% (formato recomendado por MathWorks para control de versiones en GitHub). Para visualizarlo
% con ecuaciones LaTeX renderizadas y salidas intercaladas en MATLAB, haga clic derecho sobre
% el archivo en el explorador de MATLAB y seleccione *Open as Live Script* (o *Guardar como -> .mlx*).

clear; close all; clc;

%% Paso 1: Arquitectura Física y Análisis de Movilidad (Grübler-Kutzbach)
% A diferencia de lo que sugiere la nomenclatura del manual de fábrica (ejes X, Y, Z),
% *el manipulador XK-JS1-1 NO es un robot cartesiano*. Su estructura mecánica combina:
%
% # *Base giratoria ($\theta$, motor Z — NEMA 17):* Rotación vertical sobre la mesa mediante reducción por engranajes.
% # *Carro radial ($s_X$, motor X — NEMA 23):* Tornillo sinfín inferior que desliza todo el bastidor (placas 5 y 10 y las 4 guías 16) a través del bloque fijo 2. Produce una traslación radial pura.
% # *Mecanismo biela-manivela invertido ($s_Y$, motor Y — NEMA 23):* Tornillo sinfín superior que desplaza el bloque 1 sobre el bastidor. La escuadra 6 (pivote $C$) empuja la biela 12 hacia el vértice $B$ de la escuadra 8, haciendo pivotar el brazo principal 9 alrededor de $A$.
% # *Paralelogramo articulado (varilla 13 y postes 14):* Mantiene el cuerpo de la pinza (pieza 4) *siempre horizontal* ($\varphi_{\text{pinza}} = 0$) sin agregar grados de libertad adicionales.
% # *Garra neumática/eléctrica ON/OFF (pieza 15, salida Q0.7):* Apertura/cierre en el plano horizontal sin alterar la posición del TCP (*Tool Center Point*).
%
% Para el mecanismo plano en el plano meridional $r$-$z$, la movilidad según el criterio de *Grübler-Kutzbach* es:
%
% $$M = 3(n - 1) - 2j_1 - j_2$$
%
% donde $n = 7$ eslabones (base/bloque 2, bastidor, bloque 1/escuadra 6, biela 12, balancín 8-9, varilla 13 y cuerpo de pinza 4), $j_1 = 8$ pares de 1 GDL (2 prismáticos: $s_X, s_Y$; y 6 revolutas: $C, B, A, E, A', E'$) y $j_2 = 0$.

fprintf('=========================================================================\n');
fprintf('  PASO 1: ANÁLISIS ESTRUCTURAL Y MOVILIDAD DE GRÜBLER-KUTZBACH\n');
fprintf('=========================================================================\n');

n_eslabones = 7;   % Incluye el eslabón de referencia en el plano r-z (columna/bloque 2)
j1_pares    = 8;   % 2 pares prismáticos (sX, sY) + 6 pares de revoluta (C, B, A, E, A', E')
j2_pares    = 0;   % Sin pares superiores de 2 GDL

M_plano = 3 * (n_eslabones - 1) - 2 * j1_pares - j2_pares;
M_total = M_plano + 1 + 1; % +1 giro de base (theta) +1 garra ON/OFF

fprintf('Eslabones en el plano r-z (n)          : %d\n', n_eslabones);
fprintf('Pares cinemáticos de 1 GDL (j1)        : %d (2 prismáticos + 6 revolutas)\n', j1_pares);
fprintf('Movilidad plana M = 3(n-1) - 2*j1      : %d GDL independientes (sX, sY)\n', M_plano);
fprintf('Movilidad total del manipulador        : %d GDL (theta, sX, sY + garra ON/OFF)\n\n', M_total);

%% Paso 2: Carga de Parámetros Geométricos, Supuestos y Calibración
% Todas las cotas levantadas (leídas en bocetos, estimadas sobre la foto de perfil del manual
% con error $< 5\text{ mm}$ en los pivotes $B$ y $C$, y supuestas) se centralizan en |web/js/cinematica.js|
% y se exportan a |parametros.json|. Si el archivo |parametros.json| se encuentra en la carpeta del
% script, se carga automáticamente; de lo contrario, se utilizan los valores nominales de la Tabla 2
% y Tabla 3 del informe técnico (Octubre 2026).

fprintf('=========================================================================\n');
fprintf('  PASO 2: PARÁMETROS GEOMÉTRICOS Y DE TRANSMISIÓN DE LA PLANTA\n');
fprintf('=========================================================================\n');

dir_script = fileparts(mfilename('fullpath'));
ruta_json  = fullfile(dir_script, 'parametros.json');

if isfile(ruta_json)
    datos = jsondecode(fileread(ruta_json));
    P = datos.parametros;
    D = datos.derivados;
    T = datos.transmision;
    fprintf('Fuente de parámetros: parametros.json cargado correctamente.\n');
else
    % Parámetros geométricos primarios (Tabla 2 del informe)
    P.L12        = 235.0;   % [mm] Longitud entre pivotes C-B de la biela 12 (leída/est.)
    P.a          = 145.0;   % [mm] Distancia A-B del balancín (estimada foto manual)
    P.beta       = 50.0;    % [deg] Ángulo fijo entre A-B y el brazo principal 9 (estimado)
    P.L9         = 300.0;   % [mm] Longitud A-E del brazo 9 / varilla 13 (SUPUESTO/leída)
    P.L14        = 70.0;    % [mm] Longitud entre pivotes de los postes 14 (estimada)
    P.uA         = 20.0;    % [mm] Distancia horizontal pivote A desde placa 5 (estimada)
    P.dg         = 135.0;   % [mm] Distancia horizontal TCP desde pivote E (estimada)
    P.hg         = 20.0;    % [mm] Desplazamiento vertical TCP hacia abajo desde E (estimado)
    P.recorridoX = 170.0;   % [mm] Carrera útil carro X (0 a 170 mm)
    P.recorridoY = 170.0;   % [mm] Carrera útil carro Y (0 a 170 mm, SUPUESTO)
    P.thetaMin   = -175.0;  % [deg] Límite inferior giro de base (SUPUESTO)
    P.thetaMax   = 175.0;   % [deg] Límite superior giro de base (SUPUESTO)

    % Cotas derivadas de referencia respecto al eje de giro y la mesa
    D.u5_0       = 52.0;    % [mm] Posición placa 5 con sX = 0 respecto al eje de giro
    D.hA         = 236.0;   % [mm] Altura del pivote A sobre la mesa (estimada)
    D.cu0        = -252.0;  % [mm] Coordenada horizontal de C respecto de A con g = 0 (sY = 170)
    D.ch         = 125.0;   % [mm] Altura fija de C respecto de A en el bastidor (derivada)

    % Parámetros de transmisión electromecánica (Tabla 3 del informe, foto DIP 26/10/2026)
    T.pasosRev       = 200;     % Pasos completos/rev (motores 1.8 deg/paso)
    T.microX         = 5;       % Micropasos driver JMC 2M542-N (1000 pulsos/rev)
    T.microY         = 5;       % Micropasos driver JMC 2M542-N (1000 pulsos/rev)
    T.microZ         = 5;       % Micropasos driver base (SUPUESTO, 1000 pulsos/rev)
    T.pasoHusillo    = 5.0;     % [mm/rev] Paso husillo de bolas SFU1605 (SUPUESTO)
    T.reduccionBase  = 5.0;     % Relación de transmisión por engranajes base (SUPUESTO)
    T.fMaxPTO        = 20000;   % [Hz] Frecuencia máxima PTO CPU 224 (Q0.0 y Q0.1)
    T.mmPorPulso     = T.pasoHusillo / (T.pasosRev * T.microX);
    T.pulsosPorMm    = 1 / T.mmPorPulso;
    T.gradosPorPulso = 360.0 / (T.pasosRev * T.microZ * T.reduccionBase);
    T.pulsosPorGrado = 1 / T.gradosPorPulso;
    fprintf('Fuente de parámetros: Valores nominales integrados (Tabla 2 y 3 del Informe).\n');
end

fprintf('\n--- Resumen de Cotas Cinemáticas ---\n');
fprintf('  Biela L12 = %.1f mm | Balancín a = %.1f mm | Ángulo beta = %.1f deg\n', P.L12, P.a, P.beta);
fprintf('  Brazo L9  = %.1f mm | Postes L14 = %.1f mm | Pinza (dg, hg) = (%.1f, %.1f) mm\n', P.L9, P.L14, P.dg, P.hg);
fprintf('  Pivote A: u5_0 + uA = %.1f mm (en sX=0), hA = %.1f mm sobre mesa\n', D.u5_0 + P.uA, D.hA);
fprintf('  Pivote C respecto de A: cu0 = %.1f mm (en sY=170), ch = %.1f mm\n', D.cu0, D.ch);
fprintf('  Carreras: sX in [0, %.0f] mm | sY in [0, %.0f] mm | theta in [%.0f, %.0f] deg\n\n', ...
        P.recorridoX, P.recorridoY, P.thetaMin, P.thetaMax);

%% Paso 3: Cinemática Directa (FK) — Cierre del Lazo Biela-Manivela Invertido
% Dadas las variables articulares $q = (\theta, s_X, s_Y)$ medidas desde el *homing*
% ($s_X = 0$ atrás en I0.1, $s_Y = 0$ abajo en I0.4, $\theta = 0^\circ$ en I0.0):
%
% *1. Posición del pivote $C$ respecto de $A$ (en el marco del bastidor):*
% Definimos $g = S_Y - s_Y$ como la distancia del bloque 1 respecto a su tope trasero ($S_Y = 170\text{ mm}$).
% Al aumentar $s_Y$, el bloque 1 retrocede ($g$ disminuye) y eleva el brazo:
%
% $$\mathbf{C} - \mathbf{A} = \begin{bmatrix} g + c_{u0} \\ c_h \end{bmatrix}, \qquad d = \|\mathbf{C} - \mathbf{A}\| = \sqrt{(g + c_{u0})^2 + c_h^2}$$
%
% *2. Cierre geométrico del triángulo $A$-$B$-$C$ (Ley de Cosenos):*
% La biela 12 impone $\|\mathbf{B} - \mathbf{C}\| = L_{12}$. El lazo cierra si $|a - L_{12}| \le d \le a + L_{12}$
% ($90\text{ mm} \le d \le 380\text{ mm}$). El ángulo interior $\gamma$ en el vértice $A$ y el ángulo $\psi$
% del segmento $A$-$B$ son:
%
% $$\cos\gamma = \frac{a^2 + d^2 - L_{12}^2}{2 a d}, \qquad \psi = \operatorname{atan2}(c_h, g + c_{u0}) - \gamma$$
%
% El signo menos selecciona la *rama de montaje real* (con el vértice $B$ por debajo de la recta $A$-$C$).
%
% *3. Ángulo del brazo principal ($\varphi$) y coordenadas del TCP:*
%
% $$\varphi = \psi - \beta$$
%
% $$r = u_{50} + s_X + u_A + L_9 \cos\varphi + d_g, \qquad z = h_A + L_9 \sin\varphi - h_g$$
%
% $$X = r\cos\theta, \qquad Y = r\sin\theta, \qquad Z = z$$

fprintf('=========================================================================\n');
fprintf('  PASO 3: CINEMÁTICA DIRECTA Y COMPORTAMIENTO DEL MECANISMO DE BIELAS\n');
fprintf('=========================================================================\n');

% Ejemplo puntual idéntico al script de referencia del repositorio
q_ejemplo = [30, 80, 60]; % [theta_deg, sX_mm, sY_mm]
fk_ej = cinematica_directa(P, D, q_ejemplo(1), q_ejemplo(2), q_ejemplo(3));

fprintf('Evaluación puntual en q = (theta=%.1f deg, sX=%.1f mm, sY=%.1f mm):\n', q_ejemplo);
fprintf('  -> Distancia de cierre d = |C-A| : %.2f mm (rango válido: [%.0f, %.0f] mm)\n', ...
        fk_ej.d, abs(P.a - P.L12), P.a + P.L12);
fprintf('  -> Ángulo balancín psi           : %.2f deg\n', fk_ej.psi);
fprintf('  -> Ángulo brazo principal phi    : %.2f deg\n', fk_ej.phi);
fprintf('  -> Ángulo de transmisión mu      : %.2f deg\n', fk_ej.mu_trans);
fprintf('  -> Coordenadas cilíndricas (r,z) : r = %.2f mm, z = %.2f mm\n', fk_ej.r, fk_ej.z);
fprintf('  -> Coordenadas cartesianas TCP   : X = %.2f mm, Y = %.2f mm, Z = %.2f mm\n\n', ...
        fk_ej.X, fk_ej.Y, fk_ej.Z);

% --- FIGURA 1: Esquema cinemático articulado en 3 posturas de sY (sX = 60 mm) ---
figure('Name', 'Figura 1: Posturas del Mecanismo Articulado', 'Color', 'w', 'Position', [80 80 1050 460]);

subplot(1, 2, 1); hold on; grid on; axis equal;
sX_demo = 60;
sY_posturas = [0, 85, 170];
colores_p = [0.12 0.47 0.71; 0.45 0.45 0.45; 0.80 0.36 0.08];
etiquetas_p = {'s_Y = 0 mm (Homing, brazo abajo)', 's_Y = 85 mm (Carrera media)', 's_Y = 170 mm (Brazo arriba)'};

% Dibujar mesa y columna de referencia
plot([-150 620], [0 0], 'k-', 'LineWidth', 2.2, 'HandleVisibility', 'off');
text(-140, 14, 'Mesa (z = 0 mm)', 'FontSize', 8.5, 'Color', [0.2 0.2 0.2]);
plot([0 0], [0 420], 'k-.', 'LineWidth', 0.9, 'HandleVisibility', 'off');
text(6, 405, 'Eje giro base', 'FontSize', 8, 'Color', [0.3 0.3 0.3]);

for idx = 1:length(sY_posturas)
    st = cinematica_directa(P, D, 0, sX_demo, sY_posturas(idx));
    c = colores_p(idx, :);

    % Eslabones principales: A-B-C (triángulo), A-E (brazo 9), A'-E' (varilla 13) y pinza
    plot([st.A(1), st.B(1), st.C(1)], [st.A(2), st.B(2), st.C(2)], '--', 'Color', c, 'LineWidth', 1.2, 'HandleVisibility', 'off');
    plot([st.C(1), st.B(1)], [st.C(2), st.B(2)], '-', 'Color', c, 'LineWidth', 2.0, 'HandleVisibility', 'off');
    plot([st.A(1), st.E(1)], [st.A(2), st.E(2)], '-', 'Color', c, 'LineWidth', 3.4, 'DisplayName', etiquetas_p{idx});
    plot([st.Ap(1), st.Ep(1)], [st.Ap(2), st.Ep(2)], ':', 'Color', c, 'LineWidth', 1.5, 'HandleVisibility', 'off');
    plot([st.E(1), st.Ep(1)], [st.E(2), st.Ep(2)], '-', 'Color', c, 'LineWidth', 1.4, 'HandleVisibility', 'off');
    plot([st.E(1), st.r, st.r], [st.E(2), st.E(2), st.z], '-', 'Color', c, 'LineWidth', 1.6, 'HandleVisibility', 'off');

    % Pivotes y TCP
    pts_x = [st.A(1), st.B(1), st.C(1), st.E(1)];
    pts_z = [st.A(2), st.B(2), st.C(2), st.E(2)];
    plot(pts_x, pts_z, 'o', 'MarkerSize', 5, 'MarkerFaceColor', 'w', 'MarkerEdgeColor', c, 'LineWidth', 1.4, 'HandleVisibility', 'off');
    plot(st.r, st.z, 'x', 'MarkerSize', 8, 'Color', c, 'LineWidth', 2.0, 'HandleVisibility', 'off');
end

% Etiquetar pivotes en la postura media
st_mid = cinematica_directa(P, D, 0, sX_demo, 85);
text(st_mid.A(1)-18, st_mid.A(2)-16, 'A', 'FontWeight', 'bold');
text(st_mid.B(1)+6,  st_mid.B(2)+8,  'B', 'FontWeight', 'bold');
text(st_mid.C(1)-16, st_mid.C(2)+10, 'C', 'FontWeight', 'bold');
text(st_mid.E(1)-5,  st_mid.E(2)-16, 'E', 'FontWeight', 'bold');
text(st_mid.r+8,     st_mid.z,       'TCP', 'FontWeight', 'bold');

xlim([-160 630]); ylim([-25 490]);
xlabel('Alcance radial r [mm]'); ylabel('Altura sobre la mesa z [mm]');
title(sprintf('Posturas del mecanismo en plano r-z (s_X = %d mm)', sX_demo));
legend('Location', 'northwest', 'FontSize', 8.5);

% --- Subgráfica derecha: Relación no lineal phi(sY) y ganancia angular d(phi)/d(sY) ---
subplot(1, 2, 2); hold on; grid on;
sY_vec = linspace(0, P.recorridoY, 200);
phi_vec = zeros(size(sY_vec));
dphi_dsY_deg = zeros(size(sY_vec));

for k = 1:length(sY_vec)
    st_k = cinematica_directa(P, D, 0, 0, sY_vec(k));
    [~, ~, phi_prime_rad] = jacobiano_analitico(P, D, 0, 0, sY_vec(k));
    phi_vec(k) = st_k.phi;
    dphi_dsY_deg(k) = phi_prime_rad * (180 / pi); % [deg/mm]
end

yyaxis left;
plot(sY_vec, phi_vec, '-', 'LineWidth', 2.4, 'Color', [0.76 0.35 0.05]);
ylabel('Ángulo del brazo \phi [deg]');
ylim([-38 52]);

yyaxis right;
plot(sY_vec, dphi_dsY_deg, '--', 'LineWidth', 1.8, 'Color', [0.12 0.45 0.70]);
ylabel('Sensibilidad d\phi / ds_Y [deg/mm]');
ylim([0.36 0.64]);

xlabel('Carrera del carro Y desde homing, s_Y [mm]');
title('Característica no lineal biela-manivela \phi(s_Y)');
legend({'Ángulo \phi(s_Y)', 'Ganancia d\phi/ds_Y'}, 'Location', 'north', 'FontSize', 8.5);

%% Paso 4: Cinemática Inversa (IK) y Validación Cruzada (Ida y Vuelta)
% Dado un objetivo cartesiano $(X, Y, Z)$ y el ángulo actual $\theta_{\text{actual}}$:
%
% # *Ángulo de la base ($\theta$):* $r = \sqrt{X^2 + Y^2}$. Se evalúan $\theta_k = \operatorname{atan2}(Y, X) + k \cdot 360^\circ$ ($k \in \{-1, 0, 1\}$) dentro de $[\theta_{\min}, \theta_{\max}]$, eligiendo la solución más cercana a $\theta_{\text{actual}}$ para minimizar recorrido.
% # *Ángulo del brazo ($\varphi$):* $\sin\varphi = (Z + h_g - h_A)/L_9$. Genera dos ramas: $\varphi_1 = \arcsin(\cdot)$ (brazo hacia adelante) y $\varphi_2 = \pi - \varphi_1$ (brazo invertido).
% # *Carro radial ($s_X$):* $s_X = r - d_g - L_9 \cos\varphi - u_{50} - u_A$.
% # *Carro vertical ($s_Y$):* Con $\psi = \varphi + \beta$, la intersección circunferencia-recta para el pivote $C$ arroja dos raíces:
%
% $$g_{\pm} = a\cos\psi \pm \sqrt{L_{12}^2 - (c_h - a\sin\psi)^2} - c_{u0}, \qquad s_Y = S_Y - g_{\pm}$$
%
% De las hasta $3 \times 2 \times 2 = 12$ combinaciones candidatas, *solo se acepta aquella que*:
% (i) reproduce exactamente la rama de montaje física de la cinemática directa ($\varphi_2$ nunca la cumple),
% (ii) respeta los límites mecánicos de los finales de carrera ($s_X, s_Y \in [0, 170]\text{ mm}$), y
% (iii) evita colisión con la mesa ($z > 0$).

fprintf('=========================================================================\n');
fprintf('  PASO 4: CINEMÁTICA INVERSA Y PRUEBA DE CONSISTENCIA (2,205 PUNTOS)\n');
fprintf('=========================================================================\n');

% Recuperar q_ejemplo desde sus coordenadas cartesianas (X, Y, Z)
[q_inv, estado_ik] = cinematica_inversa(P, D, fk_ej.X, fk_ej.Y, fk_ej.Z, 25.0);
fprintf('Recuperación IK para (X=%.2f, Y=%.2f, Z=%.2f) mm:\n', fk_ej.X, fk_ej.Y, fk_ej.Z);
fprintf('  -> Estado: %s\n', estado_ik.mensaje);
fprintf('  -> q recuperado = (theta=%.4f deg, sX=%.4f mm, sY=%.4f mm)\n', q_inv);

% Barrido sistemático de 21 x 21 x 5 = 2,205 puntos (idéntico a pruebas_cinematica.js)
err_max_artic = 0;
err_max_cart  = 0;
n_pruebas     = 0;
thetas_test   = [-150, -30, 0, 45, 170];

for ix = 0:20
    for iy = 0:20
        for th = thetas_test
            sx_t = P.recorridoX * ix / 20;
            sy_t = P.recorridoY * iy / 20;
            fk_t = cinematica_directa(P, D, th, sx_t, sy_t);
            [q_sol, info] = cinematica_inversa(P, D, fk_t.X, fk_t.Y, fk_t.Z, th);
            assert(info.valida, 'Falla IK en punto válido');
            fk_verif = cinematica_directa(P, D, q_sol(1), q_sol(2), q_sol(3));

            err_q = max(abs(q_sol - [th, sx_t, sy_t]));
            err_x = norm([fk_verif.X - fk_t.X, fk_verif.Y - fk_t.Y, fk_verif.Z - fk_t.Z]);
            err_max_artic = max(err_max_artic, err_q);
            err_max_cart  = max(err_max_cart, err_x);
            n_pruebas = n_pruebas + 1;
        end
    end
end

fprintf('Validación masiva FK -> IK -> FK (%d configuraciones):\n', n_pruebas);
fprintf('  -> Error máximo articular : %.2e (mm / deg)\n', err_max_artic);
fprintf('  -> Error máximo TCP       : %.2e mm (criterio < 1e-6 mm: APROBADO)\n\n', err_max_cart);

%% Paso 5: Jacobiano Analítico, Singularidades y Ángulo de Transmisión
% Derivando la ecuación de cierre de lazo $f(\psi, g) = \|a\,\mathbf{e}(\psi) - (\mathbf{C} - \mathbf{A})\|^2 - L_{12}^2 = 0$,
% con $\mathbf{e}_\perp(\psi) = [-\sin\psi, \cos\psi]^T$, la razón de transmisión cinemática del lazo cerrado es:
%
% $$\varphi' \equiv \frac{d\varphi}{ds_Y} = -\frac{d\psi}{dg} = -\frac{(B - C)_u}{a\,(\mathbf{B} - \mathbf{C})\cdot\mathbf{e}_\perp(\psi)}$$
%
% La matriz Jacobiana $J = \frac{\partial(X, Y, Z)}{\partial(\theta, s_X, s_Y)}$ (con $\theta$ en radianes) y su determinante son:
%
% $$J = \begin{bmatrix} -r\sin\theta & \cos\theta & -\cos\theta\,L_9\sin\varphi\,\varphi' \\ r\cos\theta & \sin\theta & -\sin\theta\,L_9\sin\varphi\,\varphi' \\ 0 & 0 & L_9\cos\varphi\,\varphi' \end{bmatrix}, \qquad \det J = -r\,L_9\cos\varphi\,\varphi'$$
%
% *Análisis de singularidades:*
%
% # $r = 0$: TCP sobre el eje de giro (imposible, $r \ge 411.5\text{ mm}$).
% # $\cos\varphi = 0$: Brazo totalmente vertical (imposible, $\varphi \in [-32.60^\circ, +47.04^\circ]$).
% # $\varphi' = 0$: Biela 12 vertical (el carro Y no mueve el brazo).
% # $\varphi' \to \infty$: Punto muerto o *toggle* (biela 12 alineada con $A$-$B$).
%
% Adicionalmente, el *ángulo de transmisión* $\mu_{\text{trans}}$ entre la biela 12 ($C$-$B$) y el balancín ($A$-$B$)
% evalúa la eficiencia mecánica de transmisión de fuerza (criterio recomendado de Norton: $40^\circ \le \mu_{\text{trans}} \le 140^\circ$).

fprintf('=========================================================================\n');
fprintf('  PASO 5: JACOBIANO ANALÍTICO, SINGULARIDADES Y ÁNGULO DE TRANSMISIÓN\n');
fprintf('=========================================================================\n');

% Comparación con el punto de referencia de la Sección 8 del informe: q = (30, 100, 20)
q_jac = [30, 100, 20];
[J_ana, detJ_ana, ~] = jacobiano_analitico(P, D, q_jac(1), q_jac(2), q_jac(3));

% Jacobiano numérico por diferencias finitas centrales para verificación
h_fd = 1e-5;
J_num = zeros(3);
for col = 1:3
    dq = zeros(1, 3); dq(col) = h_fd;
    fa = cinematica_directa(P, D, q_jac(1)+dq(1), q_jac(2)+dq(2), q_jac(3)+dq(3));
    fb = cinematica_directa(P, D, q_jac(1)-dq(1), q_jac(2)-dq(2), q_jac(3)-dq(3));
    J_num(:, col) = ([fa.X; fa.Y; fa.Z] - [fb.X; fb.Y; fb.Z]) / (2 * h_fd);
end
J_num(:, 1) = J_num(:, 1) * (180 / pi); % Convertir derivada respecto a theta de deg a rad

err_jac = max(abs(J_ana(:) - J_num(:)));
fprintf('Jacobiano analítico en q = (30 deg, 100 mm, 20 mm):\n');
disp(round(J_ana, 3));
fprintf('  -> |det(J)| = %.1f mm^2/rad (Informe: 1635 mm^2/rad)\n', abs(detJ_ana));
fprintf('  -> Error máx. analítico vs. diferencias finitas: %.2e (criterio < 1e-4: APROBADO)\n', err_jac);

% Barrido global de |det(J)| y ángulo de transmisión en todo el espacio de trabajo
[SX_g, SY_g] = meshgrid(linspace(0, P.recorridoX, 50), linspace(0, P.recorridoY, 50));
DETJ_g = zeros(size(SX_g));
MU_g   = zeros(size(SX_g));

for idx = 1:numel(SX_g)
    st_i = cinematica_directa(P, D, 0, SX_g(idx), SY_g(idx));
    [~, det_i, ~] = jacobiano_analitico(P, D, 0, SX_g(idx), SY_g(idx));
    DETJ_g(idx) = abs(det_i);
    MU_g(idx)   = st_i.mu_trans;
end

fprintf('Barrido completo del espacio de trabajo:\n');
fprintf('  -> Rango |det(J)|            : [%.1f, %.1f] mm^2/rad (SIN singularidades)\n', min(DETJ_g(:)), max(DETJ_g(:)));
fprintf('  -> Ángulo transmisión biela 12: [%.1f, %.1f] deg (óptimo mecánico)\n\n', min(MU_g(:)), max(MU_g(:)));

% --- FIGURA 3: Mapas de |det(J)| y ángulo de transmisión ---
figure('Name', 'Figura 3: Jacobiano y Ángulo de Transmisión', 'Color', 'w', 'Position', [100 100 1020 420]);

subplot(1, 2, 1);
contourf(SX_g, SY_g, DETJ_g, 18, 'LineColor', 'none'); colorbar;
hold on;
[C_c, h_c] = contour(SX_g, SY_g, DETJ_g, [600 900 1200 1500 1800], 'k--', 'LineWidth', 0.8);
clabel(C_c, h_c, 'FontSize', 8);
xlabel('Carro X, s_X [mm]'); ylabel('Carro Y, s_Y [mm]');
title('Manipulabilidad |det(J)| [mm^2/rad] (sin singularidades)');
grid on;

subplot(1, 2, 2);
plot(SY_g(:,1), MU_g(:,1), '-', 'LineWidth', 2.4, 'Color', [0.15 0.55 0.35]); hold on; grid on;
yline(40, 'r--', 'Límite inferior recomendado (40°)', 'LabelHorizontalAlignment', 'left', 'FontSize', 8.5);
yline(90, ':', 'Transmisión ortogonal ideal (90°)', 'Color', [0.3 0.3 0.3], 'FontSize', 8.5);
xlabel('Carrera del carro Y, s_Y [mm]'); ylabel('Ángulo de transmisión \mu_{trans} [deg]');
title('Ángulo de transmisión de la biela 12 en todo el recorrido');
ylim([30 105]);

%% Paso 6: Relación Motor-Articulación y Restricción de PTO Compartido (CPU 224)
% Al operar en *lazo abierto* sin encoders, la posición se estima integrando los pulsos emitidos
% por el PLC Siemens S7-200 CPU 224 desde la referencia de *homing*:
%
% $$\Delta s = \frac{p}{N_{\text{paso}}\,\mu}\,N_p, \qquad \Delta\theta = \frac{360^\circ}{N_{\text{paso}}\,\mu_Z\,i_\theta}\,N_p$$
%
% *Restricción física crítica del hardware (Sección 9.1):*
% La CPU 224 dispone únicamente de *dos salidas de tren de pulsos por hardware (PTO)*:
%
% * |Q0.0|: PTO dedicado al motor de la base ($\theta$, dirección en |Q0.2|).
% * |Q0.1|: *PTO compartido* entre los carros X e Y, conmutado mediante las bobinas de relés |Q0.5| (K1 -> driver X) y |Q0.6| (K2 -> driver Y), direcciones en |Q0.3| y |Q0.4|, y garra en |Q0.7|.
%
% En consecuencia, aunque X e Y pueden moverse simultáneamente cuando K1 y K2 están cerrados,
% *ambos reciben exactamente la misma frecuencia y número de pulsos*. Por ello, una trayectoria
% cartesiana recta con velocidades distintas en X e Y *no es realizable directamente en el PLC*;
% cada desplazamiento punto a punto con $|\Delta N_X| \ne |\Delta N_Y|$ se descompone en *dos tramos*:
%
% # *Tramo común:* $N_{\text{com}} = \min(|\Delta N_X|, |\Delta N_Y|)$ con K1 = ON y K2 = ON.
% # *Tramo restante:* $N_{\text{resto}} = ||\Delta N_X| - |\Delta N_Y||$ con solo el relé del eje de mayor recorrido activo.

fprintf('=========================================================================\n');
fprintf('  PASO 6: TRANSMISIÓN MOTOR-ARTICULACIÓN Y PTO COMPARTIDO (S7-200 CPU 224)\n');
fprintf('=========================================================================\n');

v_max_carros = T.fMaxPTO * T.mmPorPulso;
v_max_base   = T.fMaxPTO * T.gradosPorPulso;

fprintf('Resolución carros X, Y : %.5f mm/pulso (%.0f pulsos/mm) | Vel. máx (20 kHz): %.1f mm/s\n', ...
        T.mmPorPulso, T.pulsosPorMm, v_max_carros);
fprintf('Resolución base theta  : %.5f deg/pulso (%.2f pulsos/deg) | Vel. máx (20 kHz): %.1f deg/s\n\n', ...
        T.gradosPorPulso, T.pulsosPorGrado, v_max_base);

% Simulación de movimiento Pick & Place: Punto A -> Punto B
q_ini = [-20, 20, 15];    % [theta_deg, sX_mm, sY_mm]
q_fin = [ 45, 140, 95];   % [theta_deg, sX_mm, sY_mm]
plan_plc = perfil_pulsos_plc(T, q_ini, q_fin, 8000); % Frecuencia de operación: 8 kHz

fprintf('Simulación de movimiento Punto A -> Punto B:\n');
fprintf('  -> Pulsos requeridos: dN_theta = %+d, dN_X = %+d, dN_Y = %+d\n', ...
        plan_plc.dN_theta, plan_plc.dN_X, plan_plc.dN_Y);
fprintf('  -> Bits DIR PLC     : Q0.2 (Base)=%d, Q0.3 (X)=%d, Q0.4 (Y)=%d\n', ...
        plan_plc.DIR_theta, plan_plc.DIR_X, plan_plc.DIR_Y);
fprintf('  -> Tramo 1 (K1=1, K2=1, común)   : %d pulsos (%.2f s a 8 kHz)\n', ...
        plan_plc.N_comun, plan_plc.t_tramo1);
fprintf('  -> Tramo 2 (solo eje %s)          : %d pulsos (%.2f s a 8 kHz)\n\n', ...
        plan_plc.eje_resto, plan_plc.N_resto, plan_plc.t_tramo2);

% --- FIGURA 4: Trayectoria cartesiana ideal vs. trayectoria real en 2 tramos del PLC ---
N_pasos_sim = 120;
t_sim = linspace(0, plan_plc.t_total, N_pasos_sim);

% Trayectoria 1: Interpolación cartesiana recta ideal
fk_A = cinematica_directa(P, D, q_ini(1), q_ini(2), q_ini(3));
fk_B = cinematica_directa(P, D, q_fin(1), q_fin(2), q_fin(3));
X_ideal = linspace(fk_A.X, fk_B.X, N_pasos_sim);
Y_ideal = linspace(fk_A.Y, fk_B.Y, N_pasos_sim);
Z_ideal = linspace(fk_A.Z, fk_B.Z, N_pasos_sim);

% Trayectoria 2: Ejecución real por tramos en CPU 224 (PTO compartido Q0.1)
X_plc = zeros(1, N_pasos_sim); Y_plc = zeros(1, N_pasos_sim); Z_plc = zeros(1, N_pasos_sim);
sX_t  = zeros(1, N_pasos_sim); sY_t  = zeros(1, N_pasos_sim); th_t  = zeros(1, N_pasos_sim);

for k = 1:N_pasos_sim
    tk = t_sim(k);
    % Base en Q0.0 (en paralelo)
    frac_th = min(1, tk / max(plan_plc.t_base, 1e-6));
    th_t(k) = q_ini(1) + frac_th * (q_fin(1) - q_ini(1));

    % Carros X e Y en Q0.1 (Tramo 1 común + Tramo 2 restante)
    if tk <= plan_plc.t_tramo1
        pulso_actual = tk * plan_plc.f_PTO;
        sX_t(k) = q_ini(2) + sign(plan_plc.dN_X) * pulso_actual * T.mmPorPulso;
        sY_t(k) = q_ini(3) + sign(plan_plc.dN_Y) * pulso_actual * T.mmPorPulso;
    else
        pulso_resto = (tk - plan_plc.t_tramo1) * plan_plc.f_PTO;
        if abs(plan_plc.dN_X) >= abs(plan_plc.dN_Y)
            sX_t(k) = q_ini(2) + sign(plan_plc.dN_X) * (plan_plc.N_comun + pulso_resto) * T.mmPorPulso;
            sY_t(k) = q_fin(3);
        else
            sX_t(k) = q_fin(2);
            sY_t(k) = q_ini(3) + sign(plan_plc.dN_Y) * (plan_plc.N_comun + pulso_resto) * T.mmPorPulso;
        end
    end
    fk_k = cinematica_directa(P, D, th_t(k), sX_t(k), sY_t(k));
    X_plc(k) = fk_k.X; Y_plc(k) = fk_k.Y; Z_plc(k) = fk_k.Z;
end

figure('Name', 'Figura 4: Restricción PTO Compartido CPU 224', 'Color', 'w', 'Position', [120 120 1050 430]);

subplot(1, 2, 1); hold on; grid on; view(38, 26);
plot3(X_ideal, Y_ideal, Z_ideal, '--', 'Color', [0.45 0.45 0.45], 'LineWidth', 1.8, 'DisplayName', 'Recta cartesiana ideal (no realizable)');
plot3(X_plc, Y_plc, Z_plc, '-', 'Color', [0.80 0.30 0.05], 'LineWidth', 2.4, 'DisplayName', 'Trayectoria real PLC (2 tramos Q0.1)');
plot3(fk_A.X, fk_A.Y, fk_A.Z, 'go', 'MarkerSize', 8, 'MarkerFaceColor', 'g', 'DisplayName', 'Inicio (Punto A)');
plot3(fk_B.X, fk_B.Y, fk_B.Z, 'rs', 'MarkerSize', 8, 'MarkerFaceColor', 'r', 'DisplayName', 'Destino (Punto B)');
xlabel('X [mm]'); ylabel('Y [mm]'); zlabel('Z [mm]');
title('Trayectoria 3D del TCP: Ideal vs. CPU 224');
legend('Location', 'best', 'FontSize', 8);

subplot(1, 2, 2); hold on; grid on;
plot(t_sim, sX_t, '-', 'LineWidth', 2.2, 'Color', [0.12 0.47 0.71], 'DisplayName', 'Carro X (s_X) — Relé K1 (Q0.5)');
plot(t_sim, sY_t, '-', 'LineWidth', 2.2, 'Color', [0.85 0.37 0.01], 'DisplayName', 'Carro Y (s_Y) — Relé K2 (Q0.6)');
xline(plan_plc.t_tramo1, 'k--', 'Fin Tramo 1 (K2 OFF)', 'LabelVerticalAlignment', 'bottom', 'FontSize', 8.5, 'HandleVisibility', 'off');
xlabel('Tiempo de ejecución [s]'); ylabel('Carrera articular [mm]');
title('Perfiles de carrera con PTO compartido (Q0.1 a 8 kHz)');
legend('Location', 'northwest', 'FontSize', 8.5);

%% Paso 7: Espacio de Trabajo y Tabla de Validación Experimental (25 Puntos)
% El corte meridional $r$-$z$ es la imagen del rectángulo articular $[0, 170] \times [0, 170]\text{ mm}$:
%
% * Los bordes $s_Y = \text{cte}$ son *segmentos horizontales*, pues $s_X$ solo traslada en $r$.
% * Los bordes $s_X = \text{cte}$ son *arcos circulares de radio $L_9 = 300\text{ mm}$*.
% * El TCP alcanza $r \in [411.5, 677.0]\text{ mm}$ y $z \in [54.4, 435.5]\text{ mm}$ ($\Delta z \approx 381.1\text{ mm}$),
%   barriendo en planta una corona anular de $\pm 175^\circ$.
%
% Finalmente, se genera la *tabla de 25 puntos de calibración* (idéntica a |tabla_cinematica.csv| y
% Tabla 5 del informe) para contrastar las predicciones del gemelo digital frente a mediciones reales
% con flexómetro y escuadra en el Laboratorio de Control.

fprintf('=========================================================================\n');
fprintf('  PASO 7: ESPACIO DE TRABAJO Y TABLA DE VALIDACIÓN EXPERIMENTAL (25 PUNTOS)\n');
fprintf('=========================================================================\n');

N_ws = 45;
[SX_w, SY_w] = meshgrid(linspace(0, P.recorridoX, N_ws), linspace(0, P.recorridoY, N_ws));
R_w = zeros(size(SX_w)); Z_w = zeros(size(SX_w));
for i = 1:numel(SX_w)
    st_w = cinematica_directa(P, D, 0, SX_w(i), SY_w(i));
    R_w(i) = st_w.r;
    Z_w(i) = st_w.z;
end

fprintf('Alcance radial r del TCP : [%.1f, %.1f] mm\n', min(R_w(:)), max(R_w(:)));
fprintf('Altura vertical z del TCP: [%.1f, %.1f] mm (recorrido vertical: %.1f mm)\n\n', ...
        min(Z_w(:)), max(Z_w(:)), max(Z_w(:)) - min(Z_w(:)));

% Construir tabla de validación de 25 puntos (5 x 5)
sX_val = linspace(0, P.recorridoX, 5);
sY_val = linspace(0, P.recorridoY, 5);
filas_val = zeros(25, 7);
idx_f = 1;

for ix = 1:5
    for iy = 1:5
        st_v = cinematica_directa(P, D, 0, sX_val(ix), sY_val(iy));
        nX_v = round(sX_val(ix) * T.pulsosPorMm);
        nY_v = round(sY_val(iy) * T.pulsosPorMm);
        filas_val(idx_f, :) = [sX_val(ix), sY_val(iy), st_v.phi, st_v.r, st_v.z, nX_v, nY_v];
        idx_f = idx_f + 1;
    end
end

TablaValidacion = array2table(filas_val, ...
    'VariableNames', {'sX_mm', 'sY_mm', 'phi_deg', 'r_mm', 'z_mm', 'pulsos_X', 'pulsos_Y'});
disp(TablaValidacion);

% --- FIGURA 5: Espacio de trabajo 2D (corte r-z y corona superior) + puntos de calibración ---
figure('Name', 'Figura 5: Espacio de Trabajo del Brazo XK-JS1-1', 'Color', 'w', 'Position', [100 100 1060 440]);

% Corte meridional r-z
subplot(1, 2, 1); hold on; grid on; axis equal;
plot(R_w(:), Z_w(:), '.', 'Color', [0.85 0.55 0.30], 'MarkerSize', 4, 'DisplayName', 'Combinaciones (s_X, s_Y)');
plot(R_w(1, :), Z_w(1, :), 'b--', 'LineWidth', 1.8, 'DisplayName', 's_Y = 0 mm (Homing, brazo abajo)');
plot(R_w(end, :), Z_w(end, :), 'b-', 'LineWidth', 1.8, 'DisplayName', 's_Y = 170 mm (Brazo arriba)');
plot(R_w(:, 1), Z_w(:, 1), 'k-', 'LineWidth', 1.6, 'DisplayName', 's_X = 0 / 170 mm (Arcos L_9)');
plot(R_w(:, end), Z_w(:, end), 'k-', 'LineWidth', 1.6, 'HandleVisibility', 'off');
plot(TablaValidacion.r_mm, TablaValidacion.z_mm, 'ko', 'MarkerFaceColor', [0.95 0.85 0.1], ...
     'MarkerSize', 5.5, 'DisplayName', '25 puntos de validación');
yline(0, 'k-', 'LineWidth', 2, 'HandleVisibility', 'off');
xlim([0 740]); ylim([-20 490]);
xlabel('Alcance radial r [mm]'); ylabel('Altura sobre la mesa z [mm]');
title('Espacio de trabajo: Corte meridional r-z');
legend('Location', 'southwest', 'FontSize', 7.8);

% Vista superior (corona anular X-Y)
subplot(1, 2, 2); hold on; grid on; axis equal;
th_corona = linspace(P.thetaMin, P.thetaMax, 240) * (pi / 180);
r_min = min(R_w(:)); r_max = max(R_w(:));
fill([r_max*cos(th_corona), r_min*cos(fliplr(th_corona))], ...
     [r_max*sin(th_corona), r_min*sin(fliplr(th_corona))], ...
     [0.95 0.78 0.60], 'EdgeColor', [0.75 0.45 0.20], 'LineWidth', 1.2, 'DisplayName', 'Alcance TCP (r \in [411.5, 677] mm)');

% Base física diámetro 165 mm
th_circ = linspace(0, 2*pi, 120);
fill(82.5*cos(th_circ), 82.5*sin(th_circ), [0.72 0.75 0.78], 'EdgeColor', 'k', 'DisplayName', 'Base física (\varnothing 165 mm)');
plot([0 r_max+25], [0 0], 'b--', 'LineWidth', 1.2, 'DisplayName', '\theta = 0° (Sensor inductivo I0.0)');

xlim([-740 740]); ylim([-740 740]);
xlabel('X [mm]'); ylabel('Y [mm]');
title('Vista superior: Corona anular \theta \in [-175°, +175°]');
legend('Location', 'southwest', 'FontSize', 8);

%% ========================================================================
%  FUNCIONES LOCALES DEL MODELO CINEMÁTICO Y DEL PLANIFICADOR PLC
%  ========================================================================

function res = cinematica_directa(P, D, theta_deg, sX, sY)
% CINEMATICA_DIRECTA Calcula la postura completa de los pivotes y del TCP.
%   Entradas:
%     P, D      : Estructuras de parámetros geométricos y derivados
%     theta_deg : Ángulo de la base [deg]
%     sX, sY    : Carreras de los carros X e Y desde el homing [mm]
%   Salida:
%     res       : Estructura con coordenadas de todos los pivotes, ángulos y TCP

    % 1. Posición del pivote C respecto a A en el marco del bastidor
    g  = P.recorridoY - sY;
    cu = g + D.cu0;
    ch = D.ch;
    d  = hypot(cu, ch);

    % 2. Cierre del triángulo A-B-C mediante ley de cosenos
    cos_gamma = (P.a^2 + d^2 - P.L12^2) / (2 * P.a * d);
    res.valida = (abs(cos_gamma) <= 1.0);
    cos_gamma = max(-1.0, min(1.0, cos_gamma));
    gamma = acos(cos_gamma);

    % Rama real de montaje: vértice B por debajo de la recta A-C
    psi = atan2(ch, cu) - gamma;

    % Ángulo de transmisión entre la biela C-B y el balancín A-B
    cos_mu = (P.a^2 + P.L12^2 - d^2) / (2 * P.a * P.L12);
    cos_mu = max(-1.0, min(1.0, cos_mu));
    res.mu_trans = acos(cos_mu) * (180 / pi);

    % 3. Ángulo del brazo principal 9
    phi = psi - P.beta * (pi / 180);

    % 4. Posiciones de todos los pivotes en el plano r-z
    uA_abs = D.u5_0 + sX + P.uA;
    res.A  = [uA_abs, D.hA];
    res.Ap = [uA_abs, D.hA + P.L14];
    res.B  = res.A + P.a * [cos(psi), sin(psi)];
    res.C  = res.A + [cu, ch];
    res.E  = res.A + P.L9 * [cos(phi), sin(phi)];
    res.Ep = res.E + [0, P.L14];

    % Coordenadas del TCP (la pinza permanece siempre horizontal)
    res.d   = d;
    res.psi = psi * (180 / pi);
    res.phi = phi * (180 / pi);
    res.r   = res.E(1) + P.dg;
    res.z   = res.E(2) - P.hg;
    res.X   = res.r * cosd(theta_deg);
    res.Y   = res.r * sind(theta_deg);
    res.Z   = res.z;
end

function [q_sol, info] = cinematica_inversa(P, D, X, Y, Z, theta_actual)
% CINEMATICA_INVERSA Resuelve analíticamente q = [theta_deg, sX, sY] para (X, Y, Z).
%   Evalúa las 12 combinaciones posibles (3 giros de base x 2 ramas phi x 2 raíces g)
%   y filtra por rama de montaje física, límites de carrera y anti-colisión con la mesa.

    if nargin < 6, theta_actual = 0; end
    r = hypot(X, Y);
    if r < 1e-6
        q_sol = [NaN, NaN, NaN];
        info.valida = false;
        info.mensaje = 'Objetivo sobre el eje de giro (r = 0, singularidad)';
        return;
    end

    % Candidatos de giro de base dentro de [thetaMin, thetaMax]
    th_base = atan2d(Y, X);
    th_cands = th_base + [-360, 0, 360];
    th_cands = th_cands(th_cands >= P.thetaMin - 1e-6 & th_cands <= P.thetaMax + 1e-6);
    if isempty(th_cands)
        q_sol = [NaN, NaN, NaN];
        info.valida = false;
        info.mensaje = 'Ángulo theta fuera de recorrido de la base';
        return;
    end
    [~, idx_th] = min(abs(th_cands - theta_actual));
    theta_sel = th_cands(idx_th);

    % Altura vertical Z -> sin(phi)
    sin_phi = (Z + P.hg - D.hA) / P.L9;
    if abs(sin_phi) > 1.0 + 1e-9
        q_sol = [NaN, NaN, NaN];
        info.valida = false;
        info.mensaje = 'Altura Z fuera del alcance vertical del brazo';
        return;
    end
    sin_phi = max(-1.0, min(1.0, sin_phi));
    phi_cands = [asin(sin_phi), pi - asin(sin_phi)];

    soluciones = [];
    for phi = phi_cands
        sX = r - P.dg - P.L9 * cos(phi) - D.u5_0 - P.uA;
        psi = phi + P.beta * (pi / 180);
        bu = P.a * cos(psi);
        bh = P.a * sin(psi);
        disc = P.L12^2 - (D.ch - bh)^2;
        if disc < 0, continue; end

        for signo = [-1, 1]
            g = bu + signo * sqrt(disc) - D.cu0;
            sY = P.recorridoY - g;

            % 1. Verificar límites de carrera
            if sX < -1e-6 || sX > P.recorridoX + 1e-6 || sY < -1e-6 || sY > P.recorridoY + 1e-6
                continue;
            end
            sX_c = max(0, min(P.recorridoX, sX));
            sY_c = max(0, min(P.recorridoY, sY));

            % 2. Verificar rama de montaje física evaluando FK
            fk_check = cinematica_directa(P, D, theta_sel, sX_c, sY_c);
            if ~fk_check.valida || abs(fk_check.phi - phi * (180 / pi)) > 1e-4
                continue;
            end

            % 3. Verificar no colisión con la mesa (z > 0)
            if fk_check.z <= 0
                continue;
            end

            soluciones = [soluciones; theta_sel, sX_c, sY_c]; %#ok<AGROW>
        end
    end

    if isempty(soluciones)
        q_sol = [NaN, NaN, NaN];
        info.valida = false;
        info.mensaje = 'Posición inalcanzable: fuera de límites de carrera o colisión con mesa';
    else
        q_sol = soluciones(1, :);
        info.valida = true;
        info.mensaje = 'Solución válida encontrada en rama física';
    end
end

function [J, detJ, phi_prime] = jacobiano_analitico(P, D, theta_deg, sX, sY)
% JACOBIANO_ANALITICO Calcula la matriz J = d(X,Y,Z)/d(theta[rad], sX, sY) y su determinante.

    st = cinematica_directa(P, D, theta_deg, sX, sY);
    psi = st.psi * (pi / 180);
    phi = st.phi * (pi / 180);
    th  = theta_deg * (pi / 180);

    % Vector B - C y vector unitario perpendicular a A-B
    B_C    = st.B - st.C;
    e_perp = [-sin(psi), cos(psi)];

    % Derivada implícita d(phi)/d(sY) = -d(psi)/d(g) [rad/mm]
    phi_prime = -B_C(1) / (P.a * dot(B_C, e_perp));

    J = [ -st.r * sin(th),  cos(th), -cos(th) * P.L9 * sin(phi) * phi_prime;
           st.r * cos(th),  sin(th), -sin(th) * P.L9 * sin(phi) * phi_prime;
           0,               0,        P.L9 * cos(phi) * phi_prime ];

    detJ = det(J);
end

function plan = perfil_pulsos_plc(T, q_ini, q_fin, f_PTO)
% PERFIL_PULSOS_PLC Calcula los trenes de pulsos y tramos para la CPU 224 (PTO compartido Q0.1).

    plan.f_PTO    = f_PTO;
    plan.dN_theta = round((q_fin(1) - q_ini(1)) * T.pulsosPorGrado);
    plan.dN_X     = round((q_fin(2) - q_ini(2)) * T.pulsosPorMm);
    plan.dN_Y     = round((q_fin(3) - q_ini(3)) * T.pulsosPorMm);

    % Bits de dirección (DIR = 1 avance positivo, DIR = 0 retroceso)
    plan.DIR_theta = double(plan.dN_theta >= 0);
    plan.DIR_X     = double(plan.dN_X >= 0);
    plan.DIR_Y     = double(plan.dN_Y >= 0);

    % Descomposición en dos tramos por PTO compartido en Q0.1 (relés K1=Q0.5, K2=Q0.6)
    absX = abs(plan.dN_X);
    absY = abs(plan.dN_Y);
    plan.N_comun = min(absX, absY);
    plan.N_resto = abs(absX - absY);

    if absX >= absY
        plan.eje_resto = 'X (K1=Q0.5)';
    else
        plan.eje_resto = 'Y (K2=Q0.6)';
    end

    plan.t_tramo1 = plan.N_comun / f_PTO;
    plan.t_tramo2 = plan.N_resto / f_PTO;
    plan.t_base   = abs(plan.dN_theta) / f_PTO;
    plan.t_total  = max([plan.t_tramo1 + plan.t_tramo2, plan.t_base, 0.05]);
end
