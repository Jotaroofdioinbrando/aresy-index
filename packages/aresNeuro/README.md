# aresNeuro

Biblioteca de simulação neural para aresY.

O foco é manter a API curta e publicável no `aresy index`, sem entrar no
`stdlib/`.

O pacote traz:
- neurônio LIF discreto com sinapses densas, condutivas e exponenciais
- neurônio Hodgkin-Huxley clássico discreto
- `TimedArray`
- `PoissonGroup`
- monitor de estado e spikes

Convenção de nomes: toda função "de baixo nível" começa com `ares_` (snake_case).
Os nomes "amigáveis" (`NeuronGroup`, `Synapses`, `StateMonitor`, etc., no
estilo Brian2) são só wrappers finos que chamam a função `ares_*`
correspondente — funcionalmente idênticos, então use o que preferir.

## Structs

```aresy
struct AresLifGroup {
    n: i64,
    v: double[],
    input: double[],
    spikes: double[],
    refractory: double[],
    v_rest: double,
    v_reset: double,
    v_thresh: double,
    tau_m: double,
    tau_ref: double,
    dt: double
}

struct AresHhGroup {
    n: i64,
    v: double[],
    m: double[],
    h: double[],
    n_gate: double[],
    input: double[],
    spikes: double[],
    was_above: double[],
    c_m: double,
    g_na: double,
    g_k: double,
    g_l: double,
    e_na: double,
    e_k: double,
    e_l: double,
    dt: double,
    spike_thresh: double
}

struct AresSynapses {
    pre_n: i64,
    post_n: i64,
    w: double[][]
}

struct AresCondSynapses {
    pre_n: i64,
    post_n: i64,
    g: double[][],
    tau: double,
    e_rev: double
}

struct AresExpSynapses {
    pre_n: i64,
    post_n: i64,
    w: double[][],
    g: double[][],
    tau: double,
    dt: double
}

struct AresMonitor {
    steps: i64,
    n: i64,
    v: double[][],
    spikes: double[][],
    t: i64
}

struct AresTimedArray {
    steps: i64,
    n: i64,
    values: double[][],
    dt: double
}

struct AresPoissonGroup {
    n: i64,
    rates: double[],
    spikes: double[],
    dt: double
}
```

## Neurônio LIF (integra-e-dispara)

```aresy
fn ares_lif_group(n: i64, v_rest: double, v_reset: double, v_thresh: double, tau_m: double, tau_ref: double, dt: double) -> AresLifGroup
fn NeuronGroup(n: i64, v_rest: double, v_reset: double, v_thresh: double, tau_m: double, tau_ref: double, dt: double) -> AresLifGroup   // alias de ares_lif_group

fn ares_lif_step(g: AresLifGroup)
fn ares_lif_reset(g: AresLifGroup)

fn ares_drive(g: AresLifGroup, idx: i64, current: double)
fn ares_drive_all(g: AresLifGroup, current: double)

fn ares_lif_voltage(g: AresLifGroup, idx: i64) -> double
fn ares_lif_spike(g: AresLifGroup, idx: i64) -> double
fn ares_lif_spike_count(g: AresLifGroup) -> double
fn ares_lif_rate(g: AresLifGroup, spike_count_total: double, elapsed_ms: double) -> double
```

## Neurônio Hodgkin-Huxley clássico

Euler explícito "síncrono" (todas as derivadas usam o estado do início do
passo, igual `method='euler'` do Brian2). `dt` grande demais desestabiliza
numericamente — o próprio `ares_hh_step` lança uma exceção se `v` sair da
faixa fisiológica plausível (`-300` a `300` mV) ou virar NaN; tente
`dt <= 0.02–0.025` ms.

```aresy
fn ares_hh_group(n: i64, c_m: double, g_na: double, g_k: double, g_l: double, e_na: double, e_k: double, e_l: double, dt: double) -> AresHhGroup
fn HodgkinHuxleyGroup(n: i64, c_m: double, g_na: double, g_k: double, g_l: double, e_na: double, e_k: double, e_l: double, dt: double) -> AresHhGroup   // alias de ares_hh_group

fn ares_hh_step(g: AresHhGroup)
fn ares_hh_reset(g: AresHhGroup)
fn ares_hh_set_state(g: AresHhGroup, idx: i64, v: double, m: double, h: double, n_gate: double)

fn ares_hh_drive(g: AresHhGroup, idx: i64, current: double)
fn ares_hh_drive_all(g: AresHhGroup, current: double)

fn ares_hh_voltage(g: AresHhGroup, idx: i64) -> double
fn ares_hh_spike(g: AresHhGroup, idx: i64) -> double   // 1.0 só na borda de subida (1 spike por potencial de ação, não por passo acima do limiar)
fn ares_hh_spike_count(g: AresHhGroup) -> double
```

## Sinapses densas (peso fixo, aplicado inteiro a cada disparo)

```aresy
fn ares_dense_synapses(pre_n: i64, post_n: i64, weight: double) -> AresSynapses
fn Synapses(pre_n: i64, post_n: i64, weight: double) -> AresSynapses   // alias de ares_dense_synapses
fn ares_dense_synapses_random(pre_n: i64, post_n: i64, weight: double, p: double) -> AresSynapses   // já cria podada pra fração p das conexões

fn ares_set_weight(s: AresSynapses, i: i64, j: i64, w: double)
fn ares_get_weight(s: AresSynapses, i: i64, j: i64) -> double
fn ares_scale_weights(s: AresSynapses, factor: double)
fn ares_connect_random(s: AresSynapses, p: double)     // poda pra fração p das conexões (continua denso por baixo, O(n²))
fn ares_disconnect_self(s: AresSynapses)                // zera a diagonal (i == j)

fn ares_propagate(pre: AresLifGroup, syn: AresSynapses, post: AresLifGroup)
fn ares_run_lif(pre: AresLifGroup, syn: AresSynapses, post: AresLifGroup, mon: AresMonitor, steps: i64)
fn ares_run_poisson_lif(pre: AresPoissonGroup, syn: AresSynapses, post: AresLifGroup, mon: AresMonitor, steps: i64)
```

## Sinapses condutivas (corrente = g · (e_rev − v_pós))

```aresy
fn ares_cond_synapses(pre_n: i64, post_n: i64, weight: double, tau: double, e_rev: double) -> AresCondSynapses
fn ares_cond_synapses_random(pre_n: i64, post_n: i64, weight: double, tau: double, e_rev: double, p: double) -> AresCondSynapses

fn ares_cond_set_weight(s: AresCondSynapses, i: i64, j: i64, w: double)
fn ares_cond_get_weight(s: AresCondSynapses, i: i64, j: i64) -> double
fn ares_cond_connect_random(s: AresCondSynapses, p: double)
fn ares_cond_disconnect_self(s: AresCondSynapses)
fn ares_cond_step(s: AresCondSynapses, dt: double)       // decai a condutância; chame 1x por passo

fn ares_cond_propagate(pre: AresLifGroup, syn: AresCondSynapses, post: AresLifGroup)
fn ares_cond_propagate_hh(pre: AresHhGroup, syn: AresCondSynapses, post: AresHhGroup)   // mesma lógica, versão pra grupos Hodgkin-Huxley
fn ares_run_hh_cond(g: AresHhGroup, syn: AresCondSynapses, mon: AresMonitor, steps: i64)
```

## Sinapses exponenciais (corrente com decaimento — o modelo mais comum)

```aresy
fn ares_exp_synapses(pre_n: i64, post_n: i64, weight: double, tau: double, dt: double) -> AresExpSynapses
fn ExpSynapses(pre_n: i64, post_n: i64, weight: double, tau: double, dt: double) -> AresExpSynapses   // alias de ares_exp_synapses
fn ares_exp_synapses_random(pre_n: i64, post_n: i64, weight: double, tau: double, dt: double, p: double) -> AresExpSynapses

fn ares_exp_set_weight(s: AresExpSynapses, i: i64, j: i64, w: double)
fn ares_exp_current(s: AresExpSynapses, i: i64, j: i64) -> double
fn ares_exp_connect_random(s: AresExpSynapses, p: double)
fn ares_exp_disconnect_self(s: AresExpSynapses)

fn ares_exp_step(pre: AresLifGroup, s: AresExpSynapses, post: AresLifGroup)   // já decai + injeta em post.input; chame 1x por passo, sem precisar de ares_propagate
fn ares_run_exp_lif(pre: AresLifGroup, syn: AresExpSynapses, post: AresLifGroup, mon: AresMonitor, steps: i64)
```

## Monitor de estado e spikes

```aresy
fn ares_monitor(steps: i64, n: i64) -> AresMonitor
fn StateMonitor(steps: i64, n: i64) -> AresMonitor   // alias de ares_monitor
fn SpikeMonitor(steps: i64, n: i64) -> AresMonitor   // idem — é o mesmo struct, guarda v e spikes juntos

fn ares_monitor_v(mon: AresMonitor, g: AresLifGroup)
fn ares_monitor_spikes(mon: AresMonitor, g: AresLifGroup)
fn ares_monitor_step(mon: AresMonitor, g: AresLifGroup)       // chama as duas acima + avança mon.t
fn ares_monitor_clear(mon: AresMonitor)                        // zera mon.t (reusa o monitor sem realocar)

fn ares_hh_monitor_v(mon: AresMonitor, g: AresHhGroup)
fn ares_hh_monitor_spikes(mon: AresMonitor, g: AresHhGroup)
fn ares_hh_monitor_step(mon: AresMonitor, g: AresHhGroup)     // equivalente a ares_monitor_step, mas pra grupos HH
```

Leitura dos dados guardados: `mon.v[passo][idx]` e `mon.spikes[passo][idx]`
(ambos `double[][]`, shape `(steps, n)`).

## TimedArray (injeta uma corrente pré-definida por passo)

```aresy
fn ares_timed_array(values: double[][], dt: double) -> AresTimedArray
fn TimedArray(values: double[][], dt: double) -> AresTimedArray   // alias de ares_timed_array
fn ares_timed_array_from_shape(steps: i64, n: i64, dt: double) -> AresTimedArray   // aloca vazio (tudo 0.0), pra preencher depois com ares_timed_array_set

fn ares_timed_array_steps(ta: AresTimedArray) -> i64
fn ares_timed_array_n(ta: AresTimedArray) -> i64
fn ares_timed_array_dt(ta: AresTimedArray) -> double

fn ares_timed_array_set(ta: AresTimedArray, step: i64, idx: i64, value: double)
fn ares_timed_array_get(ta: AresTimedArray, step: i64, idx: i64) -> double
fn ares_timed_array_at(ta: AresTimedArray, step: i64, idx: i64) -> double   // alias de ares_timed_array_get
```

## PoissonGroup (spikes aleatórios com taxa média fixa)

```aresy
fn ares_poisson_group(n: i64, rate: double, dt: double) -> AresPoissonGroup                 // mesma taxa pra todo neurônio
fn PoissonGroup(n: i64, rate: double, dt: double) -> AresPoissonGroup                        // alias de ares_poisson_group
fn ares_poisson_group_rates(n: i64, rates: double[], dt: double) -> AresPoissonGroup         // uma taxa por neurônio
fn PoissonGroupRates(n: i64, rates: double[], dt: double) -> AresPoissonGroup                // alias de ares_poisson_group_rates

fn ares_poisson_set_rate(g: AresPoissonGroup, idx: i64, rate: double)
fn ares_poisson_step(g: AresPoissonGroup)
fn ares_poisson_spike_count(g: AresPoissonGroup) -> double
```

## Loops de simulação prontos (`ares_run_*`)

Cada um roda a simulação inteira num só loop (passo do neurônio pré →
propagação → passo do neurônio pós → registro no monitor), repetido `steps`
vezes — equivalente a montar esse `while` na mão, só que já pronto:

```aresy
fn ares_run_lif(pre: AresLifGroup, syn: AresSynapses, post: AresLifGroup, mon: AresMonitor, steps: i64)
fn ares_run_poisson_lif(pre: AresPoissonGroup, syn: AresSynapses, post: AresLifGroup, mon: AresMonitor, steps: i64)
fn ares_run_exp_lif(pre: AresLifGroup, syn: AresExpSynapses, post: AresLifGroup, mon: AresMonitor, steps: i64)
fn ares_run_hh(g: AresHhGroup, mon: AresMonitor, steps: i64)
fn ares_run_hh_cond(g: AresHhGroup, syn: AresCondSynapses, mon: AresMonitor, steps: i64)
```

## Exemplos

```aresy
import "aresNeuro.ay"   // localmente, se o arquivo estiver no mesmo diretório
// depois de publicar no índice:
// import aresNeuro

fn main() {
    var g = ares_lif_group(3, -65.0, -70.0, -50.0, 10.0, 2.0, 0.1)
    var syn = ares_dense_synapses(3, 3, 0.0)
    ares_set_weight(syn, 0, 1, 2.0)
    ares_set_weight(syn, 1, 2, 2.0)

    var mon = ares_monitor(100, 3)
    var t = 0
    while t < 100 {
        if t == 0 {
            ares_drive(g, 0, 20.0)
        }
        ares_lif_step(g)
        ares_propagate(g, syn, g)
        ares_monitor_step(mon, g)
        t = t + 1
    }

    print(mon.v[0][0])
    print(mon.spikes[0][0])
    return 0
}
```

HH mínimo:

```aresy
import "aresNeuro.ay"

fn main() {
    var h = ares_hh_group(1, 1.0, 120.0, 36.0, 0.3, 50.0, -77.0, -54.4, 0.1)
    ares_hh_drive(h, 0, 10.0)
    ares_hh_step(h)
    print(ares_hh_voltage(h, 0))
    return 0
}
```

Poisson + `TimedArray`:

```aresy
import "aresNeuro.ay"

fn main() {
    var ta = ares_timed_array_from_shape(4, 1, 0.1)
    ares_timed_array_set(ta, 0, 0, 5.0)
    ares_timed_array_set(ta, 1, 0, 10.0)

    var rates = darray(2)
    rates[0] = 15.0
    rates[1] = 20.0
    var pg = PoissonGroupRates(2, rates, 0.1)
    ares_poisson_step(pg)
    print(ares_poisson_spike_count(pg))
    print(ares_timed_array_get(ta, 1, 0))
    return 0
}
```
