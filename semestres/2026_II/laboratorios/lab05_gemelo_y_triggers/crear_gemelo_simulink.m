% Crea el modelo de Simulink del gemelo del brazo (gemelo_brazo.slx) y lo compara con un ensayo escalón.
% Guía 5: gemelo digital en Simulink con bloque State-Space, alimentado con el CSV de telemetría cruda.
%
%   crear_gemelo_simulink                         % usa el último CSV de ../lab04_identificacion_y_ddl/datos
%   crear_gemelo_simulink('ruta/escalon_X.csv')
%
% Modelo (laboratorio 4): x = [theta; sX; sY], u = [f0; k1*f1; k2*f1] (Hz), dx/dt = A x + B u,
% A = 0, B = diag(b_theta, b_xy, b_xy). Las entradas ya llevan el estado de los relés K1/K2, así el
% bloque State-Space es lineal e invariante. Se crean dos versiones en el mismo modelo:
%   continua   State-Space            (integradores)
%   discreta   Discrete State-Space   G = I, H = Ts*B, Ts = 25 ms (retención de orden cero, laboratorio 5)
% Requiere Simulink. Escrito sin poder ejecutarlo en la PC de desarrollo (no tiene MATLAB): si una versión
% de MATLAB cambia el nombre de un bloque, el error lo indica en la línea de add_block correspondiente.
function crear_gemelo_simulink(csv)
aqui = fileparts(mfilename('fullpath'));
if nargin < 1
    d = dir(fullfile(aqui, '..', 'lab04_identificacion_y_ddl', 'datos', 'escalon_X_*.csv'));
    if isempty(d), error('no hay ensayos: ejecute prueba_escalon.py del laboratorio 4'); end
    [~, i] = max([d.datenum]);
    csv = fullfile(d(i).folder, d(i).name);
end

% ------------------------------------------------------------ parámetros
K_theta = 190.3*180/pi;          % pulsos/rad (medido)
K_xy    = 1000/5;                % pulsos/mm (SUPUESTO: husillo de 5 mm)
bt = 1/K_theta;  bxy = 1/K_xy;
A = zeros(3);  B = diag([bt bxy bxy]);  C = eye(3);  D = zeros(3);
Ts = 0.025;
G = eye(3);  H = Ts*B;

% ------------------------------------------------------------ entrada desde el ensayo
T = readtable(csv, 'CommentStyle', '#');
t = T.t_s;
f = T.f_ordenada_hz .* T.en_movimiento;          % el tren solo existe mientras el PLC informa movimiento
eje = 'X'; if contains(csv, '_Y_'), eje = 'Y'; end
u = zeros(numel(t), 3);
if eje == 'X', u(:, 2) = f; else, u(:, 3) = f; end
sentido = sign(T.pulsos(end) - T.pulsos(1)); if sentido == 0, sentido = 1; end
u = u * sentido;
entrada = [t u];                                 % From Workspace: [tiempo, u1, u2, u3]
x0 = [0; 0; 0]; x0(2 + (eje == 'Y')) = T.pulsos(1) / K_xy;
assignin('base', 'entrada', entrada);

% ------------------------------------------------------------ modelo
mdl = 'gemelo_brazo';
if bdIsLoaded(mdl), close_system(mdl, 0); end
new_system(mdl);
set_param(mdl, 'StopTime', num2str(t(end)), 'Solver', 'ode45', 'MaxStep', '0.01');
add_block('simulink/Sources/From Workspace', [mdl '/Frecuencias'], 'VariableName', 'entrada', ...
          'Interpolate', 'off', 'Position', [40 100 140 140]);
add_block('simulink/Continuous/State-Space', [mdl '/Brazo continuo'], 'A', mat2str(A), 'B', mat2str(B), ...
          'C', mat2str(C), 'D', mat2str(D), 'X0', mat2str(x0), 'Position', [220 40 330 100]);
add_block('simulink/Discrete/Discrete State-Space', [mdl '/Brazo discreto (ZOH)'], 'A', mat2str(G), ...
          'B', mat2str(H), 'C', mat2str(C), 'D', mat2str(D), 'X0', mat2str(x0), 'SampleTime', num2str(Ts), ...
          'Position', [220 150 330 210]);
add_block('simulink/Sinks/To Workspace', [mdl '/y continuo'], 'VariableName', 'y_continuo', ...
          'SaveFormat', 'Array', 'Position', [400 55 480 85]);
add_block('simulink/Sinks/To Workspace', [mdl '/y discreto'], 'VariableName', 'y_discreto', ...
          'SaveFormat', 'Array', 'Position', [400 165 480 195]);
add_block('simulink/Sinks/Scope', [mdl '/Posiciones'], 'NumInputPorts', '2', 'Position', [400 230 440 290]);
add_line(mdl, 'Frecuencias/1', 'Brazo continuo/1', 'autorouting', 'on');
add_line(mdl, 'Frecuencias/1', 'Brazo discreto (ZOH)/1', 'autorouting', 'on');
add_line(mdl, 'Brazo continuo/1', 'y continuo/1', 'autorouting', 'on');
add_line(mdl, 'Brazo discreto (ZOH)/1', 'y discreto/1', 'autorouting', 'on');
add_line(mdl, 'Brazo continuo/1', 'Posiciones/1', 'autorouting', 'on');
add_line(mdl, 'Brazo discreto (ZOH)/1', 'Posiciones/2', 'autorouting', 'on');
save_system(mdl, fullfile(aqui, [mdl '.slx']));
fprintf('Modelo guardado: %s\n', fullfile(aqui, [mdl '.slx']));

% ------------------------------------------------------------ simulación y fidelidad
sal = sim(mdl, 'ReturnWorkspaceOutputs', 'on');
tout = sal.tout;
yc = sal.y_continuo;  yd = sal.y_discreto;
k = 2 + (eje == 'Y');
medido = interp1(t, T.pulsos / K_xy, tout, 'previous', 'extrap');
ajuste = @(y) 100 * (1 - norm(medido - y) / norm(medido - mean(medido)));
fprintf('Ensayo: %s\n', csv);
fprintf('Índice de ajuste (NRMSE) continuo: %.2f %%   discreto: %.2f %%\n', ajuste(yc(:, k)), ajuste(yd(:, k)));
fprintf('Atención: compara con la posición que informa el PLC (cuenta de pulsos). La fidelidad frente a la\n');
fprintf('planta real se obtiene con indice_fidelidad.py y las mediciones con calibre (medicion_calibre.csv).\n');
figure; stairs(t, T.pulsos / K_xy, 'k', 'LineWidth', 1); hold on;
plot(tout, yc(:, k), 'LineWidth', 1.2); plot(tout, yd(:, k), '--', 'LineWidth', 1.2);
xlabel('t [s]'); ylabel(['s_' eje ' [mm]']); grid on;
legend('PLC (cuenta de pulsos)', 'gemelo continuo', 'gemelo discreto (Ts = 25 ms)', 'Location', 'best');
end
