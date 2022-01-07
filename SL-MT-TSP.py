class Cilj:
    def __init__(self, d, r, p): # kaj imamo podano za vsak cilj: d = smer, r = cas sprostitve, p = zacetna pozicija
        self.d = d
        self.r = r
        self.p = p
        
    def pozicija(self, t, v): # pozicija cilja ob casu t, v = hitrost
        return self.p + (t - self.r) * v * self.d
    
    def __hash__(self):
        return hash((self.d, self.r, self.p))
    
    def __eq__(self, other): # preverimo enakost dveh ciljev
        return (self.d, self.r, self.p) == (other.d, other.r, other.p)
    
    def __repr__(self):
        return f"Cilj({self.d}, {self.r}, {self.p})"

class Ureditev: # načini, kako razporedimo cilje
    def __init__(self, seznam, kljuc): # seznam = vsi cilji, kljuc = funkcija, ki posortira
        self.seznam = sorted(seznam, key=kljuc)
        self.indeksi = {c: i for i, c in enumerate(self.seznam)}
        
    def __len__(self): # stevilo ciljev
        return len(self.seznam)
    
    def __getitem__(self, index): # vrne element seznama z indeksom index
        if index < 0:
            return None
        return self.seznam[index] # sigma^(-1)(index)
    
    def indeks(self, cilj): # vrne indeks nekega cilja
        return self.indeksi[cilj] # sigma(cilj)
    
class ObratnaUreditev: # obratni vrstni red razporeditve ciljev iz razreda Ureditev
    def __init__(self, ureditev):
        self.ureditev = ureditev
        
    def __len__(self):
        return len(self.ureditev)
    
    def __getitem__(self, index):
        if index < 0:
            return None
        return self.ureditev.seznam[-index-1] 
    
    def indeks(self, cilj):
        return len(self) - self.ureditev.indeks(cilj) - 1

# nekaj primerov uporabe    
# * poskrbi, da je vsak cilj določen s 3 ločenimi argumenti
cilji = [Cilj(*p) for p in zip([1, 1, -1, -1, -1, 1, -1], [0, 5, 13, 15, 6, 8, 18], [2, 5, -3, 4, 1, -2, -7])]

v = 0.3
IPO = Ureditev(cilji, lambda c: c.pozicija(0, v)) # z "lambda" navedemo neko anonimno funkcijo (lambda argumenti: funkcija)
TO = Ureditev(cilji, lambda c: (c.d, c.pozicija(0, v)))
IPOc = ObratnaUreditev(IPO)
TOc = ObratnaUreditev(TO)

print([IPOc.indeks(c) for c in cilji])
print(cilji)       
        
print(IPOc[2])
        
class SLMTTSP:
    def __init__(self, cilji, v):
        IPO = Ureditev(cilji, lambda c: c.pozicija(0, v))
        TO = Ureditev(cilji, lambda c: (c.d, c.pozicija(0, v)))
        IPOc = ObratnaUreditev(IPO)
        TOc = ObratnaUreditev(TO)
        self.v = v
        self.cilji = cilji
        self.ureditve = [IPO, IPOc, TO, TOc]
        self.F = {} # tu so shranjena stanja (C, i) in najkrajši časi, ko do tega stanja lahko pridemo (elementi se dodajajo v metodi f)
        
    def g(self, t, j, i): # najhitrejši čas obiska cilja i, če smo nazadnje obiskali cilj j ob času t
        posi = i.pozicija(t, self.v)
        posj = j.pozicija(t, self.v)
        razlika = posi - posj
        delta = 1 if razlika > 0 else -1 # hitrost gibanja agenta (pozitivna, če je razlika med zaporednima ciljema pozitivna)
        tt = t + razlika / (delta - self.v * i.d) # najmanjši potreben čas obiska i, dodan k trenutnemu času t
        if tt >= i.r:
            return (tt, [(t, posj), (tt, posi)]) # s paroma znotraj [] si zapomnimo odseke trgovčeve poti (na katerih pozicijah je bil ob časih t in tt)
        else:
            return (i.r, [(t, posj), (t + abs(i.p - posj), i.p), (i.r, i.p)]) 
        # v zadnjem primeru (srednji element seznama) agent čaka na poziciji i.p do časa i.r (v tem primeru je delta = 0)
        
    def predhodno_stanje(self, C, i):
        if i is None: # primer, ko ni predhodnega cilja
            return None
        return tuple(min(C[l], self.ureditve[l].indeks(i)) for l in range(4))
        
    def phi(self, C): # vrne vsa že obiskana mesta v naboru C
        return {j for l, m in enumerate(C) for j in self.ureditve[l][:m]} # vrne mesta, ki so bolj na začetku seznama l kot mesto m
    
    def predhodnik(self, l, C, i): # j preteče indekse vseh ureditev
        if i is None:
            return None
        CC = self.predhodno_stanje(C, i)
        obiskana = self.phi(CC)
        for j in reversed(self.ureditve[l][:CC[l]]):
            if len(obiskana.difference(self.phi(self.predhodno_stanje(CC, j)))) == 1:
                return j
        return None
        
    def f(self, C, i): # minimalni čas, da dosežemo stanje (C, i)
        if (C, i) not in self.F: 
            if C is None: # začetni pogoj
                return (0, None, None) # podatki o predhodnem koraku (ki ga tukaj ni)
            kandidati = []
            CC = self.predhodno_stanje(C, i)
            for l in range(4):
                j = self.predhodnik(l, C, i)
                t, _, _ = self.f(CC, j) # funkcija g potrebuje 3 argumente, prvi je čas, ki ga izračunamo s f
                kandidati.append((self.g(t, j, i), l, j)) 
                # vsak kandidat je določen s 3 argumenti: 
                # * rezultat funkcije g (najhitrejši čas obiska cilja i, če smo nazadnje obiskali cilj j ob času t), 
                # * indeks seznama, iz katerega je prišel naslednji obiskani cilj (l) 
                # * predhodnik (j) 
                # najmanjšega od kandidatov shranimo v F pod ključ (C, i) - pripadajoče stanje
            self.F[C, i] = min(kandidati)
        return self.F[C, i]
    
    def resi(self):
        n = len(self.cilji) # stevilo vseh ciljev
        # izvedemo f na vseh možnih naborih C za vsak cilj i
        for a in range(n):
            for b in range(n):
                for c in range(n):
                    for d in range(n):
                        for i in cilji:
                            self.f((a, b, c, d), i) # shrani v F minimalni čas, da dosežemo stanje (C, i)
        return min(self.f((n, n, n, n), i) for i in cilji) # od zaključnega stanja "nazaj" poteka rekurzija
    
    def rekonstruiraj_resitev(self):
        resitev = sorted(self.F.items(), key = lambda c: c[1]) # uredi zapise v F po časih (kdaj smo kje)
        return [C_i[1] for C_i, _ in resitev]
