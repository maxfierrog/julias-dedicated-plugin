"""Original MCAT/premed study content for the dev collection.

Written to resemble what a premed's collection actually contains, so UI work
gets exercised against realistic material:

- a downloaded-deck style cloze note type (AnKing-like: Text, Extra, Lecture
  Notes, Missed Questions, Source; grey background, custom CSS),
- stock Basic and Cloze notes, like cards a student writes herself,
- images (SVG), tables, MathJax, sub/superscripts, multi-cloze notes,
  long back sides, and hierarchical decks/tags.

`hard=True` marks notes that are notoriously easy to forget; the history
simulator makes them likely leeches.
"""

from dataclasses import dataclass, field

BB = "MCAT::1 Bio-Biochem"
CP = "MCAT::2 Chem-Phys"
PS = "MCAT::3 Psych-Soc"
ORGO = "Coursework::Organic Chemistry II"

MCAT_CLOZE = "MCAT Cloze (AnKing-style)"
BASIC = "Basic"
CLOZE = "Cloze"


@dataclass
class Note:
    notetype: str
    fields: dict[str, str]
    deck: str
    tags: list[str] = field(default_factory=list)
    hard: bool = False


def mc(
    text,
    deck,
    tags,
    extra="",
    lecture="",
    missed="",
    source="",
    hard=False,
):
    """A note from the downloaded MCAT deck."""
    return Note(
        MCAT_CLOZE,
        {
            "Text": text,
            "Extra": extra,
            "Lecture Notes": lecture,
            "Missed Questions": missed,
            "Source": source,
        },
        deck,
        tags,
        hard,
    )


def basic(front, back, deck, tags, hard=False):
    return Note(BASIC, {"Front": front, "Back": back}, deck, tags, hard)


def cloze(text, deck, tags, extra="", hard=False):
    return Note(CLOZE, {"Text": text, "Back Extra": extra}, deck, tags, hard)


def table(header, *rows):
    th = "".join(f"<th>{h}</th>" for h in header)
    trs = "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows
    )
    return f"<table><tr>{th}</tr>{trs}</table>"


AA = f"{BB}::Amino Acids and Proteins"
ENZ = f"{BB}::Enzymes"
MET = f"{BB}::Metabolism"
PHYS = f"{BB}::Physiology"
MOL = f"{BB}::Molecular Biology"
PHY = f"{CP}::Physics"
GCHEM = f"{CP}::General Chemistry"

NOTES: list[Note] = [
    # --- Amino acids and proteins ---------------------------------------
    mc(
        "The only achiral proteinogenic amino acid is {{c1::glycine}}.",
        AA,
        ["#MCAT::BB::1A", "amino_acids"],
        extra="Its side chain is a single H, so the α-carbon carries two "
        "identical substituents.",
        source="Kaplan Biochem Ch. 1",
    ),
    mc(
        "All chiral proteinogenic amino acids are {{c1::L}}-amino acids, and "
        "all except {{c2::cysteine}} have {{c3::(S)}} configuration.",
        AA,
        ["#MCAT::BB::1A", "amino_acids"],
        extra="Cysteine is (R): the sulfur in CH<sub>2</sub>SH outranks the "
        "COOH group under Cahn–Ingold–Prelog priority rules.",
        missed="AAMC FL2 B/B #31: assumed every L-amino acid is (S).",
        hard=True,
    ),
    mc(
        "The acidic amino acids are {{c1::aspartate}} and {{c1::glutamate}}; "
        "the basic amino acids are {{c2::lysine}}, {{c2::arginine}}, and "
        "{{c2::histidine}}.",
        AA,
        ["#MCAT::BB::1A", "amino_acids"],
        extra=table(
            ["Amino acid", "Side-chain pK<sub>a</sub>", "Charge at pH 7.4"],
            ["Aspartate (D)", "~3.9", "−"],
            ["Glutamate (E)", "~4.1", "−"],
            ["Histidine (H)", "~6.0", "mostly neutral"],
            ["Lysine (K)", "~10.5", "+"],
            ["Arginine (R)", "~12.5", "+"],
        ),
    ),
    mc(
        "{{c1::Histidine}} can act as a proton donor or acceptor at "
        "physiological pH because its side-chain pK<sub>a</sub> is "
        "{{c2::about 6}}.",
        AA,
        ["#MCAT::BB::1A", "amino_acids"],
        extra="This is why histidine is common in enzyme active sites "
        "(e.g., the catalytic triad of serine proteases).",
    ),
    mc(
        "{{c1::Proline}} disrupts α-helices because its side chain is bonded "
        "to the {{c2::backbone nitrogen}}, rigidifying the chain.",
        AA,
        ["#MCAT::BB::1B", "amino_acids"],
    ),
    mc(
        "Two {{c1::cysteine}} residues are {{c2::oxidized}} to form a "
        "disulfide-linked {{c3::cystine}}.",
        AA,
        ["#MCAT::BB::1A", "amino_acids"],
        lecture="Disulfide bonds are common in extracellular proteins "
        "(oxidizing environment) and rare in the cytosol (reducing).",
    ),
    mc(
        "For an amino acid with no ionizable side chain, pI is the "
        "{{c1::average of the amino and carboxyl pK<sub>a</sub> values}}.",
        AA,
        ["#MCAT::BB::1A", "amino_acids"],
        extra="Glycine: pK<sub>a1</sub> = 2.34, pK<sub>a2</sub> = 9.60, so "
        "pI ≈ (2.34 + 9.60) / 2 ≈ 5.97.",
        missed="UWorld #10422: averaged the wrong pair of pK<sub>a</sub>s for "
        "glutamate (use the two that flank the neutral form).",
        hard=True,
    ),
    mc(
        "{{c1::Secondary}} structure is stabilized by hydrogen bonds between "
        "backbone {{c2::carbonyl oxygens and amide hydrogens}}.",
        AA,
        ["#MCAT::BB::1B", "proteins"],
    ),
    mc(
        "{{c1::Tertiary}} structure is driven largely by the "
        "{{c2::hydrophobic effect}}, which buries nonpolar side chains in the "
        "protein core.",
        AA,
        ["#MCAT::BB::1B", "proteins"],
        extra="Burying nonpolar groups releases ordered water around them, "
        "increasing the entropy of the solvent.",
    ),
    mc(
        "Denaturation disrupts {{c1::secondary, tertiary, and quaternary}} "
        "structure but leaves {{c2::primary}} structure intact.",
        AA,
        ["#MCAT::BB::1B", "proteins"],
    ),
    mc(
        "The peptide bond has partial {{c1::double-bond}} character from "
        "resonance, so rotation about the C–N bond is {{c2::restricted}}.",
        AA,
        ["#MCAT::BB::1B", "proteins"],
    ),
    mc(
        "The sulfur-containing amino acids are {{c1::cysteine}} and "
        "{{c1::methionine}}.",
        AA,
        ["#MCAT::BB::1A", "amino_acids"],
    ),
    mc(
        "The aromatic amino acids are {{c1::phenylalanine, tyrosine, and "
        "tryptophan}}; {{c2::tryptophan and tyrosine}} account for most "
        "protein absorbance at 280 nm.",
        AA,
        ["#MCAT::BB::1A", "amino_acids"],
    ),
    basic(
        "Sketch a generic α-amino acid as it exists at physiological pH.",
        '<img src="amino_acid_zwitterion.svg"><br>Zwitterion: protonated '
        "amine (NH<sub>3</sub><sup>+</sup>), deprotonated carboxylate "
        "(COO<sup>−</sup>).",
        AA,
        ["#MCAT::BB::1A", "amino_acids", "self-made"],
    ),
    # --- Enzymes --------------------------------------------------------
    mc(
        "Enzymes lower the {{c1::activation energy}} of a reaction but do not "
        "change its {{c2::ΔG}} or {{c2::equilibrium constant}}.",
        ENZ,
        ["#MCAT::BB::1A", "enzymes"],
    ),
    basic(
        "What does a Michaelis–Menten plot look like, and where are "
        "V<sub>max</sub> and K<sub>m</sub>?",
        '<img src="michaelis_menten.svg"><br>Hyperbolic. V<sub>max</sub> is '
        "the plateau; K<sub>m</sub> is [S] at ½V<sub>max</sub>. Lower "
        "K<sub>m</sub> means higher affinity.",
        ENZ,
        ["#MCAT::BB::1A", "enzymes", "self-made"],
    ),
    mc(
        "K<sub>m</sub> is the substrate concentration at which velocity is "
        "{{c1::half of V<sub>max</sub>}}.",
        ENZ,
        ["#MCAT::BB::1A", "enzymes"],
    ),
    mc(
        "A {{c1::competitive}} inhibitor raises apparent K<sub>m</sub> and "
        "leaves V<sub>max</sub> unchanged.",
        ENZ,
        ["#MCAT::BB::1A", "enzymes", "inhibition"],
        extra=table(
            ["Inhibitor", "Binds", "K<sub>m</sub>", "V<sub>max</sub>"],
            ["Competitive", "Active site (E)", "↑", "—"],
            ["Noncompetitive", "Allosteric site (E or ES)", "—", "↓"],
            ["Uncompetitive", "ES only", "↓", "↓"],
            ["Mixed", "E or ES, unequal affinity", "↑ or ↓", "↓"],
        ),
        lecture="Competitive inhibition is overcome by adding more "
        "substrate; the others are not.",
        hard=True,
    ),
    mc(
        "A {{c1::noncompetitive}} inhibitor lowers V<sub>max</sub> without "
        "changing K<sub>m</sub>.",
        ENZ,
        ["#MCAT::BB::1A", "enzymes", "inhibition"],
        hard=True,
    ),
    mc(
        "An {{c1::uncompetitive}} inhibitor binds only the "
        "{{c2::enzyme–substrate complex}}, lowering both K<sub>m</sub> and "
        "V<sub>max</sub>.",
        ENZ,
        ["#MCAT::BB::1A", "enzymes", "inhibition"],
        missed="AAMC Section Bank B/B #12: picked mixed inhibition; the "
        "Lineweaver–Burk lines were parallel → uncompetitive.",
        hard=True,
    ),
    mc(
        "On a Lineweaver–Burk plot the y-intercept is "
        "{{c1::1/V<sub>max</sub>}} and the x-intercept is "
        "{{c2::−1/K<sub>m</sub>}}.",
        ENZ,
        ["#MCAT::BB::1A", "enzymes"],
    ),
    mc(
        "k<sub>cat</sub>/K<sub>m</sub> measures {{c1::catalytic "
        "efficiency}}.",
        ENZ,
        ["#MCAT::BB::1A", "enzymes"],
    ),
    mc(
        "{{c1::Cooperative}} binding produces a sigmoidal curve; a Hill "
        "coefficient {{c2::greater than 1}} indicates positive "
        "cooperativity.",
        ENZ,
        ["#MCAT::BB::1A", "enzymes"],
    ),
    mc(
        "Zymogens such as {{c1::trypsinogen}} are activated by "
        "{{c2::proteolytic cleavage}}.",
        ENZ,
        ["#MCAT::BB::1A", "enzymes"],
        extra="Trypsinogen → trypsin by enteropeptidase in the duodenum.",
    ),
    # --- Metabolism -----------------------------------------------------
    mc(
        "Glycolysis occurs in the {{c1::cytoplasm}} and nets {{c2::2 ATP}} "
        "and {{c2::2 NADH}} per glucose.",
        MET,
        ["#MCAT::BB::1D", "metabolism"],
    ),
    mc(
        "The rate-limiting enzyme of glycolysis is {{c1::phosphofructokinase-1 "
        "(PFK-1)}}.",
        MET,
        ["#MCAT::BB::1D", "metabolism", "rate_limiting"],
        extra="Activated by AMP and fructose-2,6-bisphosphate; inhibited by "
        "ATP and citrate.",
    ),
    mc(
        "The rate-limiting enzyme of the citric acid cycle is "
        "{{c1::isocitrate dehydrogenase}}.",
        MET,
        ["#MCAT::BB::1D", "metabolism", "rate_limiting"],
        hard=True,
    ),
    mc(
        "Pyruvate dehydrogenase converts pyruvate to {{c1::acetyl-CoA}}, "
        "producing {{c2::NADH and CO<sub>2</sub>}}.",
        MET,
        ["#MCAT::BB::1D", "metabolism"],
    ),
    mc(
        "The final electron acceptor of the electron transport chain is "
        "{{c1::O<sub>2</sub>}}, which is reduced to {{c2::water}}.",
        MET,
        ["#MCAT::BB::1D", "metabolism"],
    ),
    mc(
        "ATP synthase is driven by the {{c1::proton-motive force}} as "
        "H<sup>+</sup> flows from the {{c2::intermembrane space}} into the "
        "{{c2::matrix}}.",
        MET,
        ["#MCAT::BB::1D", "metabolism"],
    ),
    mc(
        "The rate-limiting enzyme of gluconeogenesis is "
        "{{c1::fructose-1,6-bisphosphatase}}.",
        MET,
        ["#MCAT::BB::1D", "metabolism", "rate_limiting"],
        hard=True,
    ),
    mc(
        "Rate-limiting enzymes: fatty acid synthesis → {{c1::acetyl-CoA "
        "carboxylase}}; β-oxidation → {{c2::carnitine acyltransferase I}}.",
        MET,
        ["#MCAT::BB::1D", "metabolism", "rate_limiting"],
        extra=table(
            ["Pathway", "Rate-limiting enzyme"],
            ["Glycolysis", "PFK-1"],
            ["Gluconeogenesis", "Fructose-1,6-bisphosphatase"],
            ["Glycogenesis", "Glycogen synthase"],
            ["Glycogenolysis", "Glycogen phosphorylase"],
            ["Citric acid cycle", "Isocitrate dehydrogenase"],
            ["Pentose phosphate", "Glucose-6-phosphate dehydrogenase"],
            ["Fatty acid synthesis", "Acetyl-CoA carboxylase"],
            ["β-oxidation", "Carnitine acyltransferase I"],
            ["Cholesterol synthesis", "HMG-CoA reductase"],
        ),
        lecture="Almost every rate-limiting step is irreversible and is "
        "where hormones exert control (insulin vs. glucagon).",
        missed="AAMC FL4 B/B #45: mixed up carnitine acyltransferase I and "
        "acetyl-CoA carboxylase under a malonyl-CoA question.",
        hard=True,
    ),
    mc(
        "The pentose phosphate pathway produces {{c1::NADPH}} and "
        "{{c2::ribose-5-phosphate}}; its rate-limiting enzyme is "
        "{{c3::glucose-6-phosphate dehydrogenase}}.",
        MET,
        ["#MCAT::BB::1D", "metabolism", "rate_limiting"],
    ),
    mc(
        "Ketone bodies are made in the {{c1::liver}} during prolonged "
        "fasting; the main ones are {{c2::acetoacetate}} and "
        "{{c2::β-hydroxybutyrate}}.",
        MET,
        ["#MCAT::BB::1D", "metabolism"],
    ),
    mc(
        "Insulin promotes {{c1::glycogenesis and lipogenesis}}; glucagon "
        "promotes {{c2::glycogenolysis and gluconeogenesis}}.",
        MET,
        ["#MCAT::BB::1D", "metabolism", "hormones"],
    ),
    # --- Physiology -----------------------------------------------------
    basic(
        "Label the phases of a neuronal action potential.",
        '<img src="action_potential.svg"><br>Resting (−70 mV) → threshold '
        "(~−55 mV) → depolarization (Na<sup>+</sup> in) → repolarization "
        "(K<sup>+</sup> out) → hyperpolarization → return to rest.",
        PHYS,
        ["#MCAT::BB::3A", "neuro", "self-made"],
    ),
    mc(
        "Depolarization is caused by opening of voltage-gated "
        "{{c1::Na<sup>+</sup>}} channels; repolarization by voltage-gated "
        "{{c2::K<sup>+</sup>}} channels.",
        PHYS,
        ["#MCAT::BB::3A", "neuro"],
    ),
    mc(
        "The Na<sup>+</sup>/K<sup>+</sup>-ATPase moves {{c1::3 Na<sup>+</sup> "
        "out}} and {{c1::2 K<sup>+</sup> in}} per ATP hydrolyzed.",
        PHYS,
        ["#MCAT::BB::3A", "neuro"],
    ),
    mc(
        "During the {{c1::absolute}} refractory period no stimulus, however "
        "strong, can trigger another action potential.",
        PHYS,
        ["#MCAT::BB::3A", "neuro"],
    ),
    basic(
        "How do the O<sub>2</sub>-binding curves of hemoglobin and "
        "myoglobin differ?",
        '<img src="oxygen_dissociation.svg"><br>Hemoglobin: sigmoidal '
        "(cooperative, 4 subunits). Myoglobin: hyperbolic, higher affinity, "
        "so it takes O<sub>2</sub> from hemoglobin in muscle.",
        PHYS,
        ["#MCAT::BB::3B", "respiratory", "self-made"],
    ),
    mc(
        "A right shift of the hemoglobin O<sub>2</sub> curve is caused by "
        "increased {{c1::CO<sub>2</sub>}}, {{c1::H<sup>+</sup>}}, "
        "{{c1::temperature}}, and {{c1::2,3-BPG}}.",
        PHYS,
        ["#MCAT::BB::3B", "respiratory"],
        extra="Mnemonic: <b>CADET, face Right</b>: CO<sub>2</sub>, Acid, "
        "2,3-DPG (BPG), Exercise, Temperature.",
    ),
    mc(
        "{{c1::Aldosterone}} increases Na<sup>+</sup> reabsorption in the "
        "distal tubule and collecting duct; {{c2::ADH}} increases water "
        "reabsorption by inserting {{c3::aquaporins}}.",
        PHYS,
        ["#MCAT::BB::3B", "renal", "hormones"],
        hard=True,
    ),
    mc(
        "Most chemical digestion occurs in the {{c1::duodenum}}; most "
        "absorption occurs in the {{c2::jejunum and ileum}}.",
        PHYS,
        ["#MCAT::BB::3B", "digestive"],
    ),
    mc(
        "Surfactant, secreted by {{c1::type II alveolar cells}}, lowers "
        "{{c2::surface tension}} in the alveoli.",
        PHYS,
        ["#MCAT::BB::3B", "respiratory"],
    ),
    mc(
        "The impulse is delayed at the {{c1::AV node}} so the ventricles can "
        "fill before contracting.",
        PHYS,
        ["#MCAT::BB::3B", "cardio"],
    ),
    mc(
        "Cortisol is a {{c1::glucocorticoid}} released by the {{c2::adrenal "
        "cortex}} in response to {{c3::ACTH}}.",
        PHYS,
        ["#MCAT::BB::3A", "endocrine", "hormones"],
    ),
    mc(
        "Steroid hormones bind {{c1::intracellular}} receptors; peptide "
        "hormones bind {{c2::cell-surface}} receptors and act through second "
        "messengers.",
        PHYS,
        ["#MCAT::BB::3A", "endocrine", "hormones"],
    ),
    mc(
        "Spermatogenesis occurs in the {{c1::seminiferous tubules}}; "
        "{{c2::Leydig}} cells secrete testosterone.",
        PHYS,
        ["#MCAT::BB::3B", "reproductive"],
        hard=True,
    ),
    # --- Molecular biology ---------------------------------------------
    mc(
        "Meiosis I separates {{c1::homologous chromosomes}}; meiosis II "
        "separates {{c2::sister chromatids}}.",
        MOL,
        ["#MCAT::BB::2B", "genetics"],
    ),
    mc(
        "Crossing over occurs in {{c1::prophase I}} of meiosis.",
        MOL,
        ["#MCAT::BB::2B", "genetics"],
    ),
    mc(
        "DNA polymerase synthesizes DNA {{c1::5′ → 3′}}, reading the "
        "template {{c2::3′ → 5′}}.",
        MOL,
        ["#MCAT::BB::1B", "molecular"],
    ),
    mc(
        "The lagging strand is made as {{c1::Okazaki fragments}}, which are "
        "joined by {{c2::DNA ligase}}.",
        MOL,
        ["#MCAT::BB::1B", "molecular"],
    ),
    mc(
        "Eukaryotic pre-mRNA processing adds a {{c1::5′ cap}} and a "
        "{{c2::3′ poly-A tail}} and removes introns by {{c3::splicing}}.",
        MOL,
        ["#MCAT::BB::1B", "molecular"],
    ),
    mc(
        "The start codon is {{c1::AUG}} (methionine); the stop codons are "
        "{{c2::UAA, UAG, and UGA}}.",
        MOL,
        ["#MCAT::BB::1B", "molecular"],
    ),
    # --- Physics ----------------------------------------------------------
    basic(
        "Displacement under constant acceleration?",
        r"\(\Delta x = v_0 t + \tfrac{1}{2} a t^2\)",
        PHY,
        ["#MCAT::CP::4A", "kinematics", "self-made"],
    ),
    mc(
        r"Work done by a constant force: \(W =\) {{c1::\(Fd\cos\theta\)}}.",
        PHY,
        ["#MCAT::CP::4A", "energy"],
    ),
    basic(
        "State Bernoulli's equation.",
        r"\(P + \tfrac{1}{2}\rho v^2 + \rho g h = \text{constant}\)",
        PHY,
        ["#MCAT::CP::4B", "fluids", "self-made"],
    ),
    mc(
        "In a horizontal pipe, where flow speed increases, pressure "
        "{{c1::decreases}} (Venturi effect).",
        PHY,
        ["#MCAT::CP::4B", "fluids"],
    ),
    mc(
        r"Continuity equation for incompressible flow: {{c1::\(A_1 v_1 = "
        r"A_2 v_2\)}}.",
        PHY,
        ["#MCAT::CP::4B", "fluids"],
    ),
    mc(
        "Resistors in series add directly; resistors in parallel add as "
        "{{c1::reciprocals}}.",
        PHY,
        ["#MCAT::CP::4C", "circuits"],
        extra=r"\(\frac{1}{R_p} = \frac{1}{R_1} + \frac{1}{R_2} + \cdots\) "
        "(capacitors are the opposite).",
    ),
    basic(
        "Capacitance of a parallel-plate capacitor?",
        r"\(C = \dfrac{\varepsilon_0 A}{d}\)",
        PHY,
        ["#MCAT::CP::4C", "circuits", "self-made"],
    ),
    mc(
        "A converging lens with the object inside the focal length forms a "
        "{{c1::virtual, upright, magnified}} image.",
        PHY,
        ["#MCAT::CP::4D", "optics"],
        lecture="Sign conventions: real images have positive i; virtual "
        "images negative. Converging lenses have positive f.",
        hard=True,
    ),
    mc(
        r"Thin lens equation: {{c1::\(\dfrac{1}{f} = \dfrac{1}{o} + "
        r"\dfrac{1}{i}\)}}.",
        PHY,
        ["#MCAT::CP::4D", "optics"],
    ),
    mc(
        "A 10× increase in sound intensity raises the sound level by "
        "{{c1::10 dB}}.",
        PHY,
        ["#MCAT::CP::4D", "sound"],
        extra=r"\(\beta = 10\log_{10}\dfrac{I}{I_0}\)",
    ),
    mc(
        "When a source and observer approach each other, the observed "
        "frequency {{c1::increases}} (Doppler effect).",
        PHY,
        ["#MCAT::CP::4D", "sound"],
    ),
    mc(
        "Alpha decay lowers mass number by {{c1::4}} and atomic number by "
        "{{c2::2}}.",
        PHY,
        ["#MCAT::CP::4E", "nuclear"],
    ),
    # --- General chemistry ---------------------------------------------
    mc(
        "ΔG = {{c1::ΔH − TΔS}}; a process is spontaneous when ΔG is "
        "{{c2::negative}}.",
        GCHEM,
        ["#MCAT::CP::5E", "thermo"],
    ),
    mc(
        "ΔG° = {{c1::−RT ln K}}.",
        GCHEM,
        ["#MCAT::CP::5E", "thermo"],
    ),
    mc(
        "Henderson–Hasselbalch: pH = pK<sub>a</sub> + "
        "{{c1::log([A<sup>−</sup>]/[HA])}}.",
        GCHEM,
        ["#MCAT::CP::5A", "acids_bases"],
    ),
    mc(
        "At the half-equivalence point of a weak-acid titration, "
        "{{c1::pH = pK<sub>a</sub>}}.",
        GCHEM,
        ["#MCAT::CP::5A", "acids_bases"],
    ),
    mc(
        "In a galvanic cell, oxidation occurs at the {{c1::anode}} and "
        "reduction at the {{c2::cathode}}.",
        GCHEM,
        ["#MCAT::CP::4C", "electrochem"],
        extra="Mnemonic: <b>An Ox, Red Cat</b>. Electrons flow anode → "
        "cathode.",
    ),
    mc(
        "Adding product to a system at equilibrium shifts it toward "
        "{{c1::reactants}}.",
        GCHEM,
        ["#MCAT::CP::5E", "equilibrium"],
    ),
    mc(
        "Real gases deviate most from ideal behavior at {{c1::high "
        "pressure}} and {{c1::low temperature}}.",
        GCHEM,
        ["#MCAT::CP::4B", "gases"],
    ),
    mc(
        "Colligative properties depend on the {{c1::number of solute "
        "particles}}, not their identity.",
        GCHEM,
        ["#MCAT::CP::5B", "solutions"],
        extra="Boiling-point elevation: ΔT<sub>b</sub> = iK<sub>b</sub>m. "
        "NaCl has i = 2; glucose has i = 1.",
    ),
    # --- Psych/Soc ------------------------------------------------------
    basic(
        "Classical conditioning",
        "Learning in which a neutral stimulus, after pairing with an "
        "unconditioned stimulus, comes to elicit a conditioned response on "
        "its own (Pavlov).",
        PS,
        ["#MCAT::PS::7C", "learning", "self-made"],
    ),
    mc(
        "{{c1::Negative reinforcement}} increases a behavior by removing an "
        "aversive stimulus.",
        PS,
        ["#MCAT::PS::7C", "learning"],
        extra=table(
            ["", "Add stimulus", "Remove stimulus"],
            ["Behavior ↑", "Positive reinforcement", "Negative reinforcement"],
            ["Behavior ↓", "Positive punishment", "Negative punishment"],
        ),
        hard=True,
    ),
    mc(
        "Piaget's stages: {{c1::sensorimotor}} → {{c2::preoperational}} → "
        "{{c3::concrete operational}} → {{c4::formal operational}}.",
        PS,
        ["#MCAT::PS::7A", "development"],
        hard=True,
    ),
    mc(
        "The fundamental attribution error overweights {{c1::dispositional}} "
        "and underweights {{c2::situational}} causes of others' behavior.",
        PS,
        ["#MCAT::PS::8B", "social_psych"],
    ),
    mc(
        "{{c1::Cognitive dissonance}} is the discomfort of holding "
        "conflicting beliefs or acting against one's beliefs.",
        PS,
        ["#MCAT::PS::7B", "attitudes"],
    ),
    basic(
        "Weber's law",
        "The just-noticeable difference is a constant proportion of the "
        "original stimulus intensity.",
        PS,
        ["#MCAT::PS::6A", "sensation", "self-made"],
    ),
    mc(
        "Erikson's adolescent stage is {{c1::identity vs. role confusion}}.",
        PS,
        ["#MCAT::PS::7A", "development"],
        hard=True,
    ),
    mc(
        "{{c1::Social facilitation}} is improved performance on simple or "
        "well-practiced tasks in the presence of others.",
        PS,
        ["#MCAT::PS::8B", "social_psych"],
    ),
    mc(
        "{{c1::Functionalism}} views society as interdependent parts that "
        "work together to maintain stability (Durkheim).",
        PS,
        ["#MCAT::PS::9A", "sociology"],
    ),
    mc(
        "The {{c1::hippocampus}} is essential for forming new explicit "
        "(declarative) memories.",
        PS,
        ["#MCAT::PS::6B", "memory"],
    ),
    mc(
        "Broca's area → {{c1::speech production}}; Wernicke's area → "
        "{{c2::language comprehension}}.",
        PS,
        ["#MCAT::PS::6B", "language"],
    ),
    mc(
        "Yerkes–Dodson law: performance peaks at {{c1::moderate}} arousal.",
        PS,
        ["#MCAT::PS::6C", "motivation"],
    ),
    # --- Coursework: Organic Chemistry II (self-made) -------------------
    basic(
        "Reagent to oxidize a 1° alcohol to an aldehyde without "
        "over-oxidation?",
        "PCC (pyridinium chlorochromate) in CH<sub>2</sub>Cl<sub>2</sub>.",
        ORGO,
        ["orgo2::oxidation"],
    ),
    basic(
        "Aldehyde + Grignard reagent, then acid workup →",
        "A 2° alcohol (formaldehyde gives a 1° alcohol; ketones give 3°).",
        ORGO,
        ["orgo2::carbonyls"],
    ),
    basic(
        "Diels–Alder reaction",
        "A [4+2] cycloaddition between a conjugated diene (s-cis) and a "
        "dienophile, forming a cyclohexene.",
        ORGO,
        ["orgo2::pericyclic"],
    ),
    basic(
        "Rank carboxylic acid derivatives by reactivity toward nucleophilic "
        "acyl substitution.",
        "Acid chloride > anhydride > ester ≈ carboxylic acid > amide.",
        ORGO,
        ["orgo2::carbonyls"],
        hard=True,
    ),
    basic(
        "What does NaBH<sub>4</sub> reduce?",
        "Aldehydes and ketones to alcohols. Not esters or carboxylic acids "
        "(those need LiAlH<sub>4</sub>).",
        ORGO,
        ["orgo2::reduction"],
    ),
    basic(
        "Aldol condensation product?",
        "A β-hydroxy carbonyl, which dehydrates on heating to an "
        "α,β-unsaturated carbonyl.",
        ORGO,
        ["orgo2::carbonyls"],
    ),
    cloze(
        "Fischer esterification: {{c1::carboxylic acid}} + {{c1::alcohol}} "
        "→ ester + water, with an {{c2::acid}} catalyst.",
        ORGO,
        ["orgo2::carbonyls"],
    ),
    cloze(
        "{{c1::Saponification}} is base-promoted hydrolysis of an ester, "
        "giving a {{c2::carboxylate salt}} and an alcohol.",
        ORGO,
        ["orgo2::carbonyls"],
        extra="Triglyceride + NaOH → glycerol + soap.",
    ),
    cloze(
        "In keto–enol tautomerism the {{c1::keto}} form is usually favored.",
        ORGO,
        ["orgo2::carbonyls"],
    ),
    cloze(
        "Enantiomers share all physical properties except "
        "{{c1::the direction they rotate plane-polarized light}}.",
        ORGO,
        ["orgo2::stereo"],
    ),
]


MCAT_CLOZE_FRONT = '<div class="card-body">{{cloze:Text}}</div>'
MCAT_CLOZE_BACK = """\
<div class="card-body">{{cloze:Text}}</div>
{{#Extra}}<hr><div class="extra">{{Extra}}</div>{{/Extra}}
{{#Lecture Notes}}<div class="hints">{{hint:Lecture Notes}}</div>{{/Lecture Notes}}
{{#Missed Questions}}<div class="hints">{{hint:Missed Questions}}</div>{{/Missed Questions}}
{{#Source}}<div class="source">{{Source}}</div>{{/Source}}
"""
MCAT_CLOZE_CSS = """\
.card {
  font-family: Arial, Helvetica, sans-serif;
  font-size: 22px;
  text-align: center;
  color: black;
  background-color: #D1CFCE;
}
.nightMode.card, .night_mode .card { background-color: #272828; color: #FFFAFA; }
.cloze { font-weight: bold; color: blue; }
.nightMode .cloze { color: #4297F9; }
.extra { font-size: 18px; color: #3a3a3a; margin-top: 8px; }
.nightMode .extra { color: #cfcfcf; }
.hints { font-size: 16px; margin-top: 10px; }
.hints a { color: #4297F9; }
.source { font-size: 12px; color: #777; margin-top: 14px; font-style: italic; }
table { border-collapse: collapse; margin: 8px auto; font-size: 16px; }
td, th { border: 1px solid #888; padding: 3px 8px; }
img { max-width: 85%; }
"""


# --- Drill sets: generated from tables, like the bulk of a real deck -----

AA_DRILL = f"{AA}::Amino Acid Drill"
AMINO_ACIDS = [
    # name, 3-letter, 1-letter, MCAT side-chain class
    ("Glycine", "Gly", "G", "nonpolar, nonaromatic"),
    ("Alanine", "Ala", "A", "nonpolar, nonaromatic"),
    ("Valine", "Val", "V", "nonpolar, nonaromatic"),
    ("Leucine", "Leu", "L", "nonpolar, nonaromatic"),
    ("Isoleucine", "Ile", "I", "nonpolar, nonaromatic"),
    ("Methionine", "Met", "M", "nonpolar, nonaromatic"),
    ("Proline", "Pro", "P", "nonpolar, nonaromatic"),
    ("Phenylalanine", "Phe", "F", "aromatic"),
    ("Tyrosine", "Tyr", "Y", "aromatic"),
    ("Tryptophan", "Trp", "W", "aromatic"),
    ("Serine", "Ser", "S", "polar"),
    ("Threonine", "Thr", "T", "polar"),
    ("Asparagine", "Asn", "N", "polar"),
    ("Glutamine", "Gln", "Q", "polar"),
    ("Cysteine", "Cys", "C", "polar"),
    ("Aspartate", "Asp", "D", "negatively charged (acidic)"),
    ("Glutamate", "Glu", "E", "negatively charged (acidic)"),
    ("Lysine", "Lys", "K", "positively charged (basic)"),
    ("Arginine", "Arg", "R", "positively charged (basic)"),
    ("Histidine", "His", "H", "positively charged (basic)"),
]
# Codes that don't follow the name's first letter are classic leeches.
_TRICKY_CODES = {"F", "Y", "W", "N", "Q", "D", "E", "K", "R"}

for _name, _three, _one, _cls in AMINO_ACIDS:
    NOTES.append(
        Note(
            "Basic (and reversed card)",
            {"Front": _name, "Back": f"{_three} · <b>{_one}</b>"},
            AA_DRILL,
            ["#MCAT::BB::1A", "amino_acids::codes"],
            hard=_one in _TRICKY_CODES,
        )
    )
    NOTES.append(
        basic(
            f"Side-chain class of <b>{_name}</b>?",
            _cls.capitalize(),
            AA_DRILL,
            ["#MCAT::BB::1A", "amino_acids::classes"],
        )
    )

ENDO = f"{BB}::Physiology::Endocrine Hormones"
HORMONES = [
    # hormone, source, main action
    (
        "ADH (vasopressin)",
        "posterior pituitary",
        "increases water reabsorption in the collecting duct",
    ),
    (
        "Oxytocin",
        "posterior pituitary",
        "stimulates uterine contraction and milk ejection",
    ),
    (
        "Growth hormone",
        "anterior pituitary",
        "promotes bone and muscle growth and raises blood glucose",
    ),
    ("Prolactin", "anterior pituitary", "stimulates milk production"),
    (
        "TSH",
        "anterior pituitary",
        "stimulates release of T<sub>3</sub>/T<sub>4</sub>",
    ),
    (
        "ACTH",
        "anterior pituitary",
        "stimulates glucocorticoid release from the adrenal cortex",
    ),
    (
        "FSH",
        "anterior pituitary",
        "stimulates follicle development and spermatogenesis",
    ),
    (
        "LH",
        "anterior pituitary",
        "triggers ovulation and testosterone production",
    ),
    (
        "T<sub>3</sub>/T<sub>4</sub>",
        "thyroid follicular cells",
        "increase basal metabolic rate",
    ),
    (
        "Calcitonin",
        "thyroid parafollicular (C) cells",
        "lowers blood Ca<sup>2+</sup>",
    ),
    ("PTH", "parathyroid glands", "raises blood Ca<sup>2+</sup>"),
    (
        "Aldosterone",
        "adrenal cortex",
        "increases Na<sup>+</sup> reabsorption and K<sup>+</sup> secretion",
    ),
    (
        "Epinephrine",
        "adrenal medulla",
        "raises heart rate and blood glucose (fight or flight)",
    ),
    ("Insulin", "pancreatic β-cells", "lowers blood glucose"),
    ("Glucagon", "pancreatic α-cells", "raises blood glucose"),
    (
        "Somatostatin",
        "pancreatic δ-cells",
        "inhibits insulin and glucagon secretion",
    ),
    ("Melatonin", "pineal gland", "regulates circadian rhythm"),
    ("Erythropoietin", "kidney", "stimulates red blood cell production"),
    (
        "ANP",
        "cardiac atria",
        "promotes Na<sup>+</sup> and water excretion, lowering blood pressure",
    ),
    ("Gastrin", "G cells of the stomach", "stimulates HCl secretion"),
    (
        "Secretin",
        "S cells of the duodenum",
        "stimulates pancreatic bicarbonate secretion",
    ),
    (
        "CCK",
        "I cells of the duodenum",
        "stimulates gallbladder contraction and pancreatic enzyme release",
    ),
]
_TRICKY_HORMONES = {"Calcitonin", "Somatostatin", "Secretin", "CCK", "ANP"}

for _h, _src, _act in HORMONES:
    NOTES.append(
        cloze(
            f"{{{{c1::{_h}}}}} is secreted by the {{{{c2::{_src}}}}} and "
            f"{{{{c3::{_act}}}}}.",
            ENDO,
            ["#MCAT::BB::3A", "endocrine::hormones"],
            hard=_h in _TRICKY_HORMONES,
        )
    )
