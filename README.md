# Sistema P2P Híbrido com Descoberta por Nó de Borda

Este é um projeto acadêmico que simula um sistema de compartilhamento de arquivos baseado em uma rede **P2P híbrida**, onde **nós regulares (peers)** se conectam a um **nó de borda (super-peer)** para registrar seus arquivos e solicitar buscas.

---

## Visão Geral

- **Peers** são responsáveis por compartilhar e requisitar arquivos.
- O **nó de borda** atua como um índice centralizado que mapeia quais peers possuem quais arquivos.
- Os peers enviam **"heartbeats" periódicos** ao nó de borda para manter a informação de arquivos atualizada.
- Quando um peer requisita um arquivo, ele consulta o nó de borda para localizar peers que possuam esse arquivo.

---

## Tecnologias Utilizadas

- Python 3.10+
- `socket`, `threading` e `json` para comunicação em rede
- Estrutura modular para reaproveitamento de código

---

## Como Executar

1. **Inicie o nó de borda**:

```bash
cd edge
cd src
python run_edge.py
```

1. **Inicie o peer**:

```bash
cd peer[1, 2, 3...]
cd src
python run_peer.py [id]
```
1. **Solicite arquivos com o script**:

```bash
python request_file.py
# Digite o nome do arquivo (ex: noticias.txt)
```

---

# Atualização via Heartbeat
Cada peer envia periodicamente sua lista de arquivos ao nó de borda, garantindo que:

O índice do nó de borda fique atualizado mesmo após novos arquivos serem recebidos.

Arquivos recém-baixados também fiquem disponíveis para outros peers