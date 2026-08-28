# aresNeuro

Biblioteca de simulação neural para aresY. API curta, sem depender do
Brian2 nem imitar o nome dele — mas pensada pra quem já conhece Brian2 se
sentir em casa (por isso as versões "apelido" tipo `NeuronGroup`,
`StateMonitor`, `Synapses` também existem, lado a lado com os nomes
`ares_*`).

O pacote traz:
- neurônio LIF (integrate-and-fire) discreto
- neurônio Hodgkin-Huxley clássico (o de verdade, com m/h/n)
- sinapses densas (peso fixo), exponenciais (com decaimento) e condutivas
  (`g * (e_rev - v)`, a mais fisiologicamente realista)
- `TimedArray` (corrente/estímulo pré-gravado por passo)
- `PoissonGroup` (spikes aleatórios com taxa configurável)
- monitor de estado (`v`) e spikes ao longo do tempo

Instala com `aresy install aresNeuro` (veja o `aresy-index`) ou importa
localmente com `import "aresNeuro.ay"` se o arquivo estiver no mesmo
diretório do seu programa.

---

## Como importar

```aresy
import "aresNeuro.ay"   // localmente, se o arquivo estiver do lado
// depois de instalado via aresy install:
// import aresNeuro
```

## Convenção de unidades

Não tem sistema de unidades embutido (ao contrário do Brian2) — os
números são só `double`, e a convenção usada nos exemplos e nos valores
default é **mV** pra tensão, **ms** pra tempo e as unidades "clássicas"
de canal (mS/cm², μA/cm² etc.) pro Hodgkin-Huxley. Você escolhe a escala;
o importante é ser consistente entre `dt`, as constantes de tempo (`tau_m`,
`tau_ref`, `tau`) e as correntes que você injeta.

---

## LIF (integrate-and-fire)

### Criar o grupo
```aresy
var g = ares_lif_group(n, v_rest, v_reset, v_thresh, tau_m, tau_ref, dt)
// ou, mais parecido com Brian2:
var g = NeuronGroup(n, v_rest, v_reset, v_thresh, tau_m, tau_ref, dt)
```
`struct AresLifGroup { n, v[], input[], spikes[], refractory[], v_rest,
v_reset, v_thresh, tau_m, tau_ref, dt }`

### Operações
| Função | O que faz |
|---|---|
| `ares_drive(g, idx, current)` | injeta corrente em UM neurônio (some, e é zerada a cada `ares_lif_step`) |
| `ares_drive_all(g, current)` | injeta a mesma corrente em todos os neurônios |
| `ares_lif_step(g)` | avança um passo de `dt` (Euler explícito) |
| `ares_lif_voltage(g, idx)` | lê `v` de um neurônio |
| `ares_lif_spike(g, idx)` | `1.0` se disparou nesse passo, senão `0.0` |
| `ares_lif_spike_count(g)` | soma de disparos de todos os neurônios nesse passo |
| `ares_lif_reset(g)` | volta todo mundo pro estado inicial (`v_reset`, sem refratário) |
| `ares_lif_rate(g, spike_count_total, elapsed_ms)` | taxa de disparo (Hz) a partir de uma contagem acumulada |

**Importante — corrente é zerada a cada passo.** `ares_lif_step` zera
`g.input[i]` no final. Se você quer uma corrente constante ao longo da
simulação (tipo o `I` de uma equação do Brian2), precisa chamar
`ares_drive`/`ares_drive_all` **dentro do loop, a cada iteração** — não
só uma vez antes do `while`.

**Refratário**: discretizado do mesmo jeito que o Brian2 discretiza
`unless refractory` — o passo do disparo já conta como o primeiro tick da
janela refratária, então depois do disparo o código segura por
`tau_ref - dt`, não `tau_ref` inteiro. (Isso foi corrigido recentemente;
se você tem uma cópia antiga da lib com uma contagem de spikes ~3.5% mais
alta que o esperado, é essa a causa — atualiza.)

---

## Hodgkin-Huxley

### Criar o grupo
```aresy
var g = ares_hh_group(n, c_m, g_na, g_k, g_l, e_na, e_k, e_l, dt)
// ou:
var g = HodgkinHuxleyGroup(n, c_m, g_na, g_k, g_l, e_na, e_k, e_l, dt)
```
`struct AresHhGroup { n, v[], m[], h[], n_gate[], input[], spikes[],
was_above[], c_m, g_na, g_k, g_l, e_na, e_k, e_l, dt, spike_thresh }`

Todo neurônio nasce em `v = -65.0` com `m, h, n_gate` já nos valores de
equilíbrio fisiológico clássicos do HH em repouso (`0.0529`, `0.596`,
`0.3177`) — não precisa inicializar isso na mão.

As equações de taxa (`alpha_m`, `beta_m`, etc.) usam `v` **absoluto**
(direto em mV, repouso em -65mV), já com o deslocamento do potencial de
repouso embutido nas constantes. Isso é diferente das fórmulas clássicas
de Hodgkin & Huxley (1952), que foram derivadas pra uma variável
deslocada (repouso em 0). Se for comparar com um script Brian2 escrito
"colando" as fórmulas de 1952 direto, lembra de aplicar esse
deslocamento (`V = v + 65`) nas equações do Brian2 também, senão os dois
modelos não são a mesma física — só parecem, na superfície.

### Operações
| Função | O que faz |
|---|---|
| `ares_hh_drive(g, idx, current)` | injeta corrente em UM neurônio (zerada a cada passo) |
| `ares_hh_drive_all(g, current)` | injeta em todos |
| `ares_hh_step(g)` | avança um passo de `dt` |
| `ares_hh_voltage(g, idx)` | lê `v` |
| `ares_hh_spike(g, idx)` | `1.0` se cruzou o limiar de disparo NESSE passo (borda de subida — o platô do potencial de ação não conta várias vezes) |
| `ares_hh_spike_count(g)` | soma de disparos nesse passo |
| `ares_hh_reset(g)` | volta tudo pro estado de repouso |
| `ares_hh_set_state(g, idx, v, m, h, n_gate)` | força um estado inicial customizado num neurônio |

**Ordem de integração**: `ares_hh_step` usa Euler explícito **síncrono**
— todas as derivadas (`m`, `h`, `n`, `v`) usam o estado do início do
passo; tudo é atualizado só no final. É o mesmo jeito que o `method='euler'`
do Brian2 discretiza, então os dois batem bem próximo (diferença residual
de arredondamento, não de modelo).

**Estabilidade numérica — leia isto antes de escolher `dt`.** O sistema
HH é "stiff" (o gate `m` reage muito mais rápido que os outros perto do
limiar), e Euler explícito só é **condicionalmente estável**: acima de um
certo `dt` crítico, a simulação diverge pra valores absurdos ou `NaN` em
poucos passos. Na prática (parâmetros clássicos):
- `dt <= 0.02–0.025 ms`: seguro, erro de discretização pequeno
- `dt` entre `0.03` e `0.07 ms`: ainda converge, mas com erro visível (a tensão final já desvia vários mV do valor "verdadeiro")
- `dt >= 0.08 ms` (pros parâmetros clássicos): instável, diverge

Se `dt` for grande demais, `ares_hh_step` agora **detecta e lança uma
exceção** (`throw`) em vez de deixar o resultado virar `NaN` silenciosamente
— dá pra capturar com `try`/`catch` se quiser reagir (ex.: tentar de novo
com `dt` menor).

---

## Sinapses

Três tipos, cada um com seu jeito de propagar o efeito de um spike:

### Densas (peso fixo, soma direto na corrente)
```aresy
var syn = ares_dense_synapses(pre_n, post_n, weight)   // ou Synapses(...)
ares_set_weight(syn, i, j, w)
ares_get_weight(syn, i, j)
ares_scale_weights(syn, factor)
ares_propagate(pre, syn, post)   // só funciona entre AresLifGroup
```

### Exponenciais (corrente com decaimento entre spikes)
```aresy
var syn = ares_exp_synapses(pre_n, post_n, weight, tau, dt)  // ou ExpSynapses(...)
ares_exp_set_weight(syn, i, j, w)
ares_exp_current(syn, i, j)
ares_exp_step(pre, syn, post)    // decai + propaga, só entre AresLifGroup
```

### Condutivas (a mais realista — `g * (e_rev - v)`)
```aresy
var syn = ares_cond_synapses(pre_n, post_n, weight, tau, e_rev)
ares_cond_set_weight(syn, i, j, w)
ares_cond_get_weight(syn, i, j)
ares_cond_step(syn, dt)              // decai a condutância entre spikes
ares_cond_propagate(pre, syn, post)      // pre/post do tipo AresLifGroup
ares_cond_propagate_hh(pre, syn, post)   // pre/post do tipo AresHhGroup
```

**Cuidado com `ares_cond_step`.** `ares_cond_synapses` já cria a matriz
`g` inteira preenchida com `weight` (não começa em zero, e não existe
uma função que "recarregue" `g[i][j]` a cada spike como a exponencial
faz). Ou seja: `ares_cond_propagate*` injeta corrente toda vez que o
pré-sináptico dispara, usando o valor de `g` que estiver ali naquele
momento — se você também chamar `ares_cond_step` a cada passo, a
condutância vai decaindo pra zero com o tempo e a sinapse "murcha"
mesmo continuando a disparar. Só chama `ares_cond_step` se for essa a
dinâmica que você quer (ex.: simular fadiga sináptica); pra uma sinapse
condutiva de peso constante, não chama.

**Por que existe `ares_cond_propagate` E `ares_cond_propagate_hh`
separados**: o aresY não tem sobrecarga de função (não dá pra ter dois
`fn` com o mesmo nome recebendo tipos de struct diferentes), então uma
sinapse condutiva conectando neurônios HH precisa da variante `_hh`. Se
você tentar `ares_cond_propagate` com um `AresHhGroup`, o compilador
recusa em tempo de compilação com uma mensagem clara — não é silencioso.
Densas e exponenciais, por enquanto, só têm a versão LIF (não tem
`ares_propagate_hh`/`ares_exp_step_hh` ainda).

---

## Monitores

```aresy
var mon = ares_monitor(steps, n)     // ou StateMonitor(...) / SpikeMonitor(...)

// a cada passo da simulação:
ares_monitor_step(mon, g)            // LIF: grava v[t][i] e spikes[t][i]
ares_hh_monitor_step(mon, g)         // HH: idem

// ou separado, se só quiser um dos dois:
ares_monitor_v(mon, g)               // só v (LIF)
ares_monitor_spikes(mon, g)          // só spikes (LIF)
ares_hh_monitor_v(mon, g)            // só v (HH)
ares_hh_monitor_spikes(mon, g)       // só spikes (HH)

ares_monitor_clear(mon)              // reseta o cursor de tempo do monitor pra 0

// leitura depois:
print(mon.v[passo][neuronio])
print(mon.spikes[passo][neuronio])
```
`struct AresMonitor { steps, n, v[][], spikes[][], t }` — `mon.t` é o
cursor interno (quantos passos já foram gravados); passar do `steps`
lança `throw` ("monitor cheio").

---

## TimedArray (estímulo pré-gravado)

Útil pra reproduzir exatamente a mesma sequência de corrente em vários
neurônios/simulações, ou importar um estímulo gerado fora do aresY.

```aresy
var ta = ares_timed_array_from_shape(steps, n, dt)   // aloca vazio
ares_timed_array_set(ta, passo, idx, valor)
// ...preenche...
var v = ares_timed_array_get(ta, passo, idx)         // ou _at, é alias

// ou já construindo a partir de uma matriz double[][] pronta:
var ta2 = ares_timed_array(matriz, dt)               // ou TimedArray(...)
```
`struct AresTimedArray { steps, n, values[][], dt }`

---

## PoissonGroup (spikes aleatórios)

```aresy
var pg = ares_poisson_group(n, rate, dt)             // taxa igual pra todos
// ou taxa por neurônio:
var rates = darray(n)
rates[0] = 15.0
// ...
var pg2 = ares_poisson_group_rates(n, rates, dt)      // ou PoissonGroupRates(...)

ares_poisson_set_rate(pg, idx, rate)
ares_poisson_step(pg)                // sorteia spikes nesse passo (rate*dt = prob.)
ares_poisson_spike_count(pg)
```
`struct AresPoissonGroup { n, rates[], spikes[], dt }`. Usa `random()` do
compilador — não é reprodutível entre execuções (sem seed fixa hoje).

---

## Atalhos "rode tudo de uma vez"

Pra simulações simples sem precisar escrever o `while` manualmente:
```aresy
ares_run_lif(pre, syn, post, mon, steps)          // LIF + sinapse densa
ares_run_poisson_lif(pre, syn, post, mon, steps)  // Poisson -> LIF, sinapse densa
ares_run_exp_lif(pre, syn, post, mon, steps)      // LIF + sinapse exponencial
ares_run_hh(g, mon, steps)                        // HH sozinho, sem sinapse
ares_run_hh_cond(g, syn, mon, steps)              // HH recorrente + sinapse condutiva (g conectado nele mesmo)
```
Pra qualquer coisa mais customizada (injetar corrente variável por
passo, misturar tipos de sinapse, redes LIF+HH juntas), escreve o `while`
na mão — é só umas 5 linhas, e os exemplos abaixo mostram o padrão.

---

## Exemplos

### LIF com sinapse densa
```aresy
import "aresNeuro.ay"

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

### HH mínimo, com corrente constante
```aresy
import "aresNeuro.ay"

fn main() {
    var h = ares_hh_group(1, 1.0, 120.0, 36.0, 0.3, 50.0, -77.0, -54.4, 0.01)
    var t = 0
    while t < 5000 {
        ares_hh_drive(h, 0, 10.0)   // precisa injetar A CADA passo
        ares_hh_step(h)
        t = t + 1
    }
    print(ares_hh_voltage(h, 0))
    return 0
}
```

### Rede HH recorrente com sinapse condutiva
```aresy
import "aresNeuro.ay"

fn main() {
    var n = 100
    var g = HodgkinHuxleyGroup(n, 1.0, 120.0, 36.0, 0.3, 50.0, -77.0, -54.4, 0.01)
    var syn = ares_cond_synapses(n, n, 0.05, 5.0, 0.0)
    var mon = StateMonitor(2000, n)

    var t = 0
    while t < 2000 {
        var i = 0
        while i < n {
            ares_hh_drive(g, i, 10.0)
            i = i + 1
        }
        ares_hh_step(g)
        ares_cond_propagate_hh(g, syn, g)   // note o _hh no final
        ares_hh_monitor_step(mon, g)
        t = t + 1
    }

    print(ares_hh_voltage(g, 0))
    return 0
}
```

### Poisson + TimedArray
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

---

## Limitações conhecidas

- Sem sistema de unidades — números crus, você garante a consistência.
- `random()` do PoissonGroup não tem seed configurável (sem reprodutibilidade).
- Sinapses densas e exponenciais não têm variante `_hh` ainda (só a
  condutiva tem `ares_cond_propagate_hh`); conectar HH com essas duas
  exige adaptar a função na mão por enquanto.
- Sem sinapses esparsas — todas as matrizes de peso são densas
  (`pre_n × post_n`), então redes muito grandes gastam memória O(n²)
  mesmo com poucas conexões reais.
- Sem plasticidade sináptica (STDP e afins).
- HH só tem Euler explícito — sem um integrador implícito/adaptativo,
  `dt` pequeno é obrigatório pra estabilidade (ver seção acima).
