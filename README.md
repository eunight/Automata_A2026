# Autómata de Control Interoperable para Cajero Automático

**Universidad:** Universidad de Los Andes (ULA) - Facultad de Ingeniería  
**Escuela:** Escuela de Ingeniería de Sistemas  
**Materia:** Teoría de la Computación (Semestre A 2026)  
**Integrantes:** Ramón Belandria y Eugenia Ramirez  

---

## 1. Descripción del Proyecto

Este proyecto implementa el sistema de control de un cajero automático operando como un elemento de borde en una red bancaria. El objetivo principal es establecer un protocolo de intercambio de mensajes entre el cajero (cliente) y el sistema central del banco (servidor), garantizando funciones críticas como retiro de efectivo, consulta de saldo y cambio de clave de seguridad.

El sistema ha sido validado mediante la composición síncrona de autómatas, asegurando un diseño libre de interbloqueos lógicos y con manejo estricto de casos de borde.

## 2. Abstracción Matemática: Máquinas de Mealy

Dado que el cajero es un sistema reactivo que requiere emitir mensajes a la red en tiempo real, el uso de un Autómata Finito Determinístico (AFD) clásico es insuficiente. La arquitectura se fundamenta en **Máquinas de Mealy**, donde cada transición no solo altera el estado del sistema, sino que genera una salida explícita.

### 2.1. Definición Formal del Cajero (Cliente)
El transductor local se define como la tupla de 6 elementos $M_c = (Q_c, \Sigma_c, \Gamma_c, \delta_c, \lambda_c, q_0)$:

*   **$Q_c$ (Estados):** $\{q0, q1, q1\_wait, q2, q2\_wait, q\_menu, q\_cons\_wait, q\_cons, q\_ret, q\_ret\_wait, q\_disp, q\_cam, q\_cam\_wait, q\_blok\}$
*   **$\Sigma_c$ (Alfabeto de Entrada):** Interacciones físicas y respuestas de red $\{t, p, vok, verr, opc, opr, opk, nk, m, sok, serr, f\}$.
*   **$\Gamma_c$ (Alfabeto de Salida):** Accionadores locales y peticiones de red $\{pedir\_pin, enviar\_pin\_banco, solicitar\_saldo\_banco, \dots \}$.
*   **$\delta_c$ (Función de Transición):** $\delta_c: Q_c \times \Sigma_c \rightarrow Q_c$
*   **$\lambda_c$ (Función de Salida):** $\lambda_c: Q_c \times \Sigma_c \rightarrow \Gamma_c$
*   **$q_0$ (Estado Inicial):** $q0$ (Reposo)

### 2.2. Definición Formal del Banco (Servidor)
El comportamiento del lado del servidor se modela como $M_b = (Q_b, \Sigma_b, \Gamma_b, \delta_b, \lambda_b, b\_reposo)$:

*   **$Q_b$ (Estados):** $\{b\_reposo, b\_autenticando, b\_verificando\_fondos\}$
*   **$\Sigma_b$ (Alfabeto de Entrada):** Peticiones de la red $\{enviar\_pin\_banco, solicitar\_fondos\_banco, solicitar\_saldo\_banco, solicitar\_cambio\_banco\}$.
*   **$\Gamma_b$ (Alfabeto de Salida):** Respuestas del sistema central $\{vok, verr, sok, serr\}$.

## 3. Protocolo de Intercambio (Composición)

La interoperabilidad se logra componiendo ambos transductores. El alfabeto de salida del cajero intersecta con el alfabeto de entrada del banco ($\Gamma_c \cap \Sigma_b \neq \emptyset$), y viceversa. 

Cuando $M_c$ ejecuta una transición que genera $\gamma \in \Gamma_c$ destinada a la red, $M_c$ transita a un estado asíncrono de espera (ej. $q\_ret\_wait$). El símbolo $\gamma$ es consumido inmediatamente como entrada $\sigma \in \Sigma_b$ por $M_b$, el cual procesa la lógica central y emite una respuesta $\gamma_b \in \Gamma_b$ (ej. $sok$ o $serr$). Esta respuesta saca a $M_c$ de su estado de espera, completando el ciclo transaccional.

*Nota de Arquitectura (Manejo de Desconexiones): En una implementación física, los estados de espera ($q\_X\_wait$) deben incorporar una transición $\epsilon$ o de timeout ($t_{out}$) hacia un estado de error local para evitar "deadlocks" si el enlace con el servidor ($M_b$) se interrumpe.*

## 4. Diagramas de Estado

### 4.1. Máquina de Mealy: Cajero Automático
```mermaid
stateDiagram-v2
    direction TB
    q0 : q0 (Reposo)
    q1 : q1 (Ingreso PIN)
    q1_wait : q1_wait (Espera Banco)
    q2 : q2 (Reintento PIN)
    q2_wait : q2_wait (Espera Banco)
    q_menu : q_menu (Menú Principal)
    q_cons_wait : q_cons_wait (Espera Saldo)
    q_cons : q_cons (Consulta)
    q_ret : q_ret (Retiro)
    q_ret_wait : q_ret_wait (Espera Fondos)
    q_disp : q_disp (Dispensar e Imprimir)
    q_cam : q_cam (Cambio Clave)
    q_cam_wait : q_cam_wait (Espera Confirmación)
    q_blok : q_blok (Bloqueo)

    [*] --> q0
    q0 --> q1 : t / pedir_pin
    q1 --> q1_wait : p / enviar_pin_banco
    q1_wait --> q_menu : vok / mostrar_menu
    q1_wait --> q2 : verr / pedir_pin_intento2
    q2 --> q2_wait : p / enviar_pin_banco
    q2_wait --> q_menu : vok / mostrar_menu
    q2_wait --> q_blok : verr / retener_tarjeta
    
    q_menu --> q_cons_wait : opc / solicitar_saldo_banco
    q_cons_wait --> q_cons : vok / mostrar_saldo
    q_cons --> q0 : f / expulsar_tarjeta
    
    q_menu --> q_ret : opr / pedir_monto
    q_ret --> q_ret_wait : m / solicitar_fondos_banco
    q_ret_wait --> q_disp : sok / entregar_dinero_e_imprimir
    q_ret_wait --> q_menu : serr / fondos_insuficientes
    q_disp --> q0 : f / expulsar_tarjeta
    
    q_menu --> q_cam : opk / pedir_nueva_clave
    q_cam --> q_cam_wait : nk / solicitar_cambio_banco
    q_cam_wait --> q_menu : vok / cambio_exitoso
    q_cam_wait --> q_menu : verr / mostrar_menu
    
    q_menu --> q0 : f / expulsar_tarjeta
    q_blok --> [*]

```

### 4.2. Máquina de Mealy: Servidor Bancario

```mermaid
stateDiagram-v2
    direction LR
    b_reposo : b_reposo (Espera)
    b_auth : b_autenticando (Verificación)
    b_fondos : b_verificando_fondos (Consultando BD)

    [*] --> b_reposo
    b_reposo --> b_auth : enviar_pin_banco / procesando...
    b_auth --> b_reposo : ok / vok (o verr)
    b_reposo --> b_fondos : solicitar_fondos_banco / procesando...
    b_fondos --> b_reposo : ok / sok (o serr)
    b_reposo --> b_reposo : solicitar_saldo_banco / vok
    b_reposo --> b_reposo : solicitar_cambio_banco / vok (o verr)

```

## 5. Ejecución del Simulador

### 5.1. Requisitos

* Python 3.10+
* Archivos de configuración: `automata_cajero.txt` y `automata_banco.txt` en el mismo directorio.

### 5.2. Uso

Ejecutar el archivo principal del simulador interactivo:

```bash
python simulador.py

```

El entorno de simulación permite forzar respuestas negativas del banco en tiempo real escribiendo el comando `error` en la consola, facilitando la auditoría de los casos límite de denegación de fondos y bloqueo por superación de intentos fallidos.

```

```
