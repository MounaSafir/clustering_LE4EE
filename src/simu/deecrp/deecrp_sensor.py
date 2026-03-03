from math import dist
from simu.sensors import Sensors, State, OutOfEnergy
from simu.messsage import Message


class DeecrpSensors(Sensors):

    def __init__(self, position, id, config, use_routing=True):  # Mettre routing a True ou False
        super().__init__(position, id, config)


        self.w1 = 0.5
        self.w2 = 0.3
        self.w3 = 0.2


        self.is_CH = False
        self.my_ch = None
        self.cluster_members = set()


        self.use_routing = use_routing
        self.next_hop = None

        self.debug = False

    def compute_density(self, pos, neighbors_pos):
        if not neighbors_pos:
            return 0.0

        avg = sum(dist(pos, p) for p in neighbors_pos) / len(neighbors_pos)
        d_max = dist(
            (self.config.min_x, self.config.min_y),
            (self.config.max_x, self.config.max_y)
        )
        return max(0.0, min(1.0, (d_max - avg) / d_max))

 
    def fitness(self, energy, pos, density):
        p1 = energy / self.config.EI

        d_bs = dist(pos, (self.config.bs_x, self.config.bs_y))
        d_max = dist(
            (self.config.min_x, self.config.min_y),
            (self.config.max_x, self.config.max_y)
        )
        p2 = (d_max - d_bs) / d_max

        return self.w1 * p1 + self.w2 * p2 + self.w3 * density


    def compute_Eth(self, k):
        L = self.config.PACKET_SIZE
        d_bs = dist(self.position, (self.config.bs_x, self.config.bs_y))

        E_rx = k * self.config.E_RX * L
        E_da = k * self.config.E_DA * L

        if d_bs < self.config.d0:
            E_tx = L * self.config.E_TX + L * self.config.E_FS * d_bs**2
        else:
            E_tx = L * self.config.E_TX + L * self.config.E_MP * d_bs**4

        return E_rx + E_da + E_tx


    def select_next_hop(self, ch_infos):
        d_bs = dist(self.position, (self.config.bs_x, self.config.bs_y))
        d_max = dist(
            (self.config.min_x, self.config.min_y),
            (self.config.max_x, self.config.max_y)
        )
        best = None
        best_score = score = (
                0.5 * (self.er/ self.config.EI) +
                0.5 * ((d_max - d_bs) / d_max)
            )

        for cid, info in ch_infos.items():
            if cid == self.id:
                continue

            d_iBS = dist((self.config.bs_x, self.config.bs_y), info["pos"])
            if d_iBS >= d_bs:
                continue

            score = (
                0.5 * (info["energy"] / self.config.EI) +
                0.5 * ((d_max - d_iBS) / d_max)
            )

            if score > best_score:
                best_score = score
                best = cid

        return best
    

    def aggregate(self, timeout=1):
        now = self.simpy_env.now
        aggregates = [0]

        while self.simpy_env.now - now < timeout:
            msg = yield from self.receive(5)
            while msg:

                if msg.tag == "DATA":
                    if msg.data["my_ch"] == self.id:
                        self.config.environment.metric.event_received_by_ch()
                        aggregates.append(msg.data["value"])

                        E = self.config.E_DA * self.config.PACKET_SIZE
                        self.er -= E
                        if self.er <= 1e-6:
                            raise OutOfEnergy()
          
                elif self.use_routing and msg.tag == "ROUTE_DATA" and self.is_CH:
                    if self.debug:
                        self.print(
                        f"RELAY DATA | size={len(msg.data)} | next_hop={self.next_hop}"
                    )
                    aggregates.extend(msg.data)

                msg = yield from self.receive()

        return aggregates


    def iteration(self):

        # par securite
        if self.er <= 1e-6:
            self.state = State.DEAD
            return


        if self.debug:
            self.print(
                f"START | er={self.er:.2f} | is_CH={self.is_CH} | my_ch={self.my_ch}"
            )
        # devrais je rester CH ?

        if self.is_CH:
            if self.er > self.compute_Eth(len(self.cluster_members)):
                if self.debug:
                    self.print(
                        f"KEEP_CH | members={len(self.cluster_members)} | Eth={self.compute_Eth(len(self.cluster_members)):.2f}"
        )
                self.send(self.config.RANGE, Message(
                    self.id, self.simpy_env.now,
                    "KEEP_CH", self.id, self.config.PACKET_SIZE
                ))
                return
            else:
                self.is_CH = False
                self.my_ch = None
                self.cluster_members.clear()
                self.next_hop = None
                if self.debug:
                    self.print(
                        f"DROP_CH | er={self.er:.2f} < Eth={self.compute_Eth(len(self.cluster_members)):.2f}"
                    )

        # J attends pour recevoir les KEEP_CH
        if self.my_ch is not None:
            msg = yield from self.receive(1)
            if msg and msg.tag == "KEEP_CH" and msg.data == self.my_ch:
                return
            else:
                self.my_ch = None

        # Je fais ma compagne

        self.send(self.config.RANGE, Message(
            self.id, self.simpy_env.now,
            "CH_ADV",
            {"energy": self.er, "pos": self.position},
            self.config.PACKET_SIZE
        ))

        # Je recupere mes candidats

        candidates = []
        msg = yield from self.receive(3)
        while msg:
            if msg.tag == "CH_ADV":
                candidates.append(msg)
            msg = yield from self.receive(1)

        neighbors_pos = [m.data["pos"] for m in candidates]

        scored = []
        scored.append((
            self.fitness(self.er, self.position,
                         self.compute_density(self.position, neighbors_pos)),
            self.id
        ))

        for m in candidates:
            scored.append((
                self.fitness(m.data["energy"], m.data["pos"],
                             self.compute_density(m.data["pos"], neighbors_pos)),
                m.sender
            ))

        scored.sort(key=lambda x: x[0], reverse=True)

        # Je boucle sur mes candidats pour rejoindre le meilleur CH
        for _, cid in scored:
            if cid == self.id:
                self.is_CH = True
                self.my_ch = self.id
                self.cluster_members.clear()
                break

            self.send(self.config.RANGE, Message(
                self.id, self.simpy_env.now,
                "JOIN_REQ", self.id, self.config.PACKET_SIZE
            ))

            reply = yield from self.receive(2)
            if reply and reply.tag == "JOIN_OK":
                self.my_ch = cid
                if self.debug:
                    self.print(f"JOINED CH {cid}")
                return

        if self.my_ch is None:
            self.is_CH = True
            self.my_ch = self.id
            self.cluster_members.clear()

        # Si je suis CH j'accepte les membres
        if self.is_CH:
            deadline = self.simpy_env.now + 2
            while self.simpy_env.now < deadline:
                msg = yield from self.receive(1)
                if msg and msg.tag == "JOIN_REQ":
                    self.cluster_members.add(msg.sender)
                    if self.debug:
                        self.print(
                            f"ACCEPT MEMBER {msg.sender} | members={len(self.cluster_members)}"
        )
                    self.send(self.config.RANGE, Message(
                        self.id, self.simpy_env.now,
                        "JOIN_OK", self.id, self.config.PACKET_SIZE
                    ))




        # La partie routage

        if self.is_CH and self.use_routing:
            self.send(self.config.RANGE, Message(
                self.id, self.simpy_env.now,
                "CH_INFO",
                {"energy": self.er, "pos": self.position},
                self.config.PACKET_SIZE
            ))

            ch_infos = {}
            msg = yield from self.receive(3)
            while msg:
                if msg.tag == "CH_INFO":
                    ch_infos[msg.sender] = msg.data
                msg = yield from self.receive(1)

            self.next_hop = self.select_next_hop(ch_infos)
        else:
            self.next_hop = None
        
        if self.debug:
            if self.is_CH:
                self.print(
                    f"CH FINAL | members={sorted(self.cluster_members)} | next_hop={self.next_hop}"
                )
            else:
                self.print(f"MEMBER | my_ch={self.my_ch}")


    


    def end_iteration(self):
        
        self.state = State.SLEEP
