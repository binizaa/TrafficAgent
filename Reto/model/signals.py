# ── CONTROLADOR DE SEMÁFOROS ──────────────────────────────────────────────────

class FourWaySignals:
    def __init__(self, green_ns, green_ew, yellow, all_red):
        self.g     = int(green_ns)
        self.y     = int(yellow)
        self.ar    = int(all_red)
        self.phase = 0
        self.sub   = 'G'
        self.t_in  = 0
        self.t     = 0

    def lights(self):
        L = {d: 'R' for d in [
            'G263','G279','G468','G680',
            'Y468','Y263','Y1064','Y680','P279',
            'B468','B263','B1064','B680',
            'O680','O279','O263','O1064',
        ]}
        if self.phase == 0:
            for d in ['O680','O279','O263','O1064']:          L[d] = self.sub
        elif self.phase == 1:
            for d in ['G263','G279','G468','G680']:           L[d] = self.sub
        elif self.phase == 2:
            for d in ['Y468','Y263','Y1064','Y680','P279']:   L[d] = self.sub
        elif self.phase == 3:
            for d in ['B468','B263','B1064','B680']:          L[d] = self.sub
        return L

    def step(self):
        self.t += 1
        if   self.sub == 'G'  and self.t_in >= self.g:
            self.sub, self.t_in = 'Y', 0
        elif self.sub == 'Y'  and self.t_in >= self.y:
            self.sub, self.t_in = 'AR', 0
        elif self.sub == 'AR' and self.t_in >= self.ar:
            self.phase = (self.phase + 1) % 4
            self.sub, self.t_in = 'G', 0
        else:
            self.t_in += 1

    @property
    def phase_name(self):
        phases = {0: "Norte-Sur", 1: "Este-Oeste", 2: "Diagonal Y", 3: "Diagonal B"}
        return phases.get(self.phase, "?")
