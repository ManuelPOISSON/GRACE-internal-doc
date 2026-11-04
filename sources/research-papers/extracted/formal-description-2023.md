---
document_type: research_paper
paper_id: formal-description-2023
title: The Meta Attack Language - A Formal Description
authors: Wojciech Wideł; Simon Hacks; Mathias Ekstedt; Pontus Johnson; Robert Lagerström
year: 2023
doi: 10.1016/j.cose.2023.103284
source_url: https://doi.org/10.1016/j.cose.2023.103284
pdf: ../pdfs/malformaldescription.pdf
extraction_mode: raw_with_headings
sha256: 2c0811bf65f012927a679f2961dc887abbd7d62e593af6ec1e4923a582a9f64c
pages: 12
---

## Page 1

Computers & Security 130 (2023) 103284
Contents lists available at ScienceDirect
Computers & Security
journal homepage: www.elsevier.com/locate/cose
The meta attack language - a formal description
Wojciech Wideła
, Simon Hacksb,∗
, Mathias Ekstedta
, Pontus Johnsona
, Robert Lagerströma
a
Division of Network and Systems Engineering, KTH Royal Institute of Technology,Stockholm, Sweden
b
Department of Computer and Systems Sciences, Stockholm University, Stockholm, Sweden
a r t i c l e i n f o
Article history:
Received 27 January 2023
Revised 24 April 2023
Accepted 28 April 2023
Available online 2 May 2023
Keywords:
Threat modeling
Attack simulation
Attack graphs
Domain speciﬁc language
a b s t r a c t
Nowadays, IT infrastructures are involved in making innumerable aspects of our lives convenient, starting
with water or energy distribution systems, and ending with e-commerce solutions and online banking
services. In the worst case, cyberattacks on such infrastructures can paralyze whole states and lead to
losses in terms of both human lives and money.
One of the approaches to increase security of IT infrastructures relies on modeling possible ways of
compromising them by potential attackers. To facilitate creation and reusability of such models, domain
speciﬁc languages (DSLs) can be created. Ideally, a user will employ a DSL for modeling their infrastruc-
ture of interest, with the domain-speciﬁc threats and attack logic being already encoded in the DSL by
the domain experts.
The Meta Attack Language (MAL) has been introduced previously as a meta-DSL for development of
security-oriented DSLs. In this work, we deﬁne formally the syntax and a semantics of MAL to ease a
common understanding of MAL’s functionalities and enable reference implementations on different tech-
nical platforms. It’s applicability for modeling and analysis of security of IT infrastructures is illustrated
with an example.
© 2023 The Author(s). Published by Elsevier Ltd.
This is an open access article under the CC BY license (http://creativecommons.org/licenses/by/4.0/)
### 1. Introduction
Assessing the level of security in various forms of computer sys-
tems is a challenging activity. In fact, the diﬃculty starts already
at the deﬁnition of what security means and how it should be
measured. One approach for measuring and analyzing security that
lately has gained popularity, both in academia and in practice, is
attack graphs. Attack graphs describe how an (imagined) antago-
nist can move in a system by taking different actions. In its sim-
plest form the actions are combined in a graph by means of OR
and AND gates capturing the logical dependencies between the ac-
tions. With the attack vectors resulting from this type of modeling,
it is possible for security engineers to understand and assess weak
links in the overall defense of larger system architectures.
Even though potentially valuable for the security engineers,
generally it is quite costly to make use of the attack graphs due to
their poor reusability. In previous work (Johnson et al., 2018), we
have introduced the Meta Attack Language (MAL) as a meta do-
main speciﬁc language (meta-DSL) to support the development of
domain speciﬁc languages (DSLs) for attack graph generation and
∗
Corresponding author.
E-mail addresses: widel@kth.se (W. Wideł), simon.hacks@dsv.su.se (S. Hacks),
mekstedt@kth.se (M. Ekstedt), pontusj@kth.se (P. Johnson), robertl@kth.se (R. Lager-
ström).
attack simulations. MAL formalizes how modeling languages can
be devised so that speciﬁc attack graph instances can be automati-
cally generated from system architecture models described accord-
ing to a speciﬁc meta model.
By providing MAL as a meta-DSL, it is easier to create DSLs
that can solely focus on representing domain related aspects, while
already providing the frame for modelling the security aspects.
Even better, by providing an ecosystem of DSLs developed with
MAL (Hacks and Katsikeas, 2021), language developers are able to
reuse existing concepts and reﬁne them towards the needs of the
certain domain. Moreover, an existing tool (Ekstedt et al., 2015) has
already been further developed to support MAL-based DSLs to al-
low eﬃcient computation of attack paths based on the provided
instantiation of the MAL DSL.
In this paper, we introduce a formal description of the syntax
and semantics of MAL. Thus, we describe the functional aspects of
MAL in greater detail and we aim to unify the understanding of
MAL among its different stakeholders. Moreover, we want to pro-
vide a technology independent description of MAL to enable its im-
plementation in different technologies. Accordingly, we opted for a
formalization in set notation and not in technology speciﬁc nota-
tions as for example xtext.1
1
https://www.eclipse.org/Xtext/
https://doi.org/10.1016/j.cose.2023.103284
0167-4048/© 2023 The Author(s). Published by Elsevier Ltd. This is an open access article under the CC BY license (http://creativecommons.org/licenses/by/4.0/)

## Page 2

W. Wideł, S. Hacks, M. Ekstedt et al. Computers & Security 130 (2023) 103284
In previous works, syntax and semantics were only brieﬂy
sketched (Johnson et al., 2018) to a level that would not allow pro-
viding another implementation of MAL. Instead, the idea of MAL
was sketched and illustrated by an informal example. Other works
did not elaborate on MAL itself but were solely using it to create
MAL DSLs (e.g., Hacks et al., 2020; Katsikeas et al., 2019; Katsikeas
et al., 2022) or provide methods for the developing of MAL DSLs
(e.g., Hacks and Katsikeas, 2021; Hacks et al., 2023; Xiong et al.,
2021).
The paper starts off with Section 2 providing an overview of
MAL. In Section 3, we report on related work, before we present
an example model in Section 4 that is used throughout the main
contributions of the paper presented in Section 5 and 6 that cover
the syntax and semantics of MAL. In Section 7, we perform some
exemplary calculations based on the example model before the pa-
per is concluded.
### 2. An informal introduction to MAL
MAL could be thought of as a language combining UML class
and object diagrams and probabilistic attack-defense graphs. The
basic elements of MAL are Assets, which are described in
a concrete MAL DSL and correspond to classes, that can have
Instances, which are represented in models adhering to a con-
crete MAL DSL and correspond to objects. E.g., an Asset Com-
puter could have an Instance MyMacBook. Assets can have
Associations to one another so that a Computer can Communi-
cate over a Network. As in class diagrams, the Associations fea-
ture Roles and Multiplicities, where the latter govern how
many Instances can be Linked to each other.
In addition to this standard UML structure, MAL also features
Attack steps that are located on the Assets. E.g., a Com-
puter could have the Attack steps Connect and Compromise.
Attack steps are of either AND or OR type and can have par-
ents and children so that they can form attack graphs. Further-
more, MAL includes Defenses that can be related to the Attack
steps when forming the graph. So, our Computer might be de-
fended by being Patched, and with this defense in place it makes
sense to introduce two Attack steps on the Computer: Exploit-
KnownVulnerability and ExploitZeroDayVulnerability. In order to en-
code how diﬃcult it is for an attacker to succeed with the different
Attack steps, for instance given available Defenses, MAL also
allows the language designer to specify a Time To Compromise
(TTC) for Attack steps. As mentioned earlier, MAL adopts a
probabilistic approach, so we may for instance specify that we be-
lieve that the time it takes to succeed with ExploitZeroDayVulner-
ability follows a certain probability distribution, perhaps Exponen-
tial(0.01) days. However, any other probability distribution or com-
bination of probability distributions can be used to describe the
likelihood of a successful attack step and the needed effort by the
attacker, which need to be deﬁned by the MAL DSL developer fol-
lowing for example (Xiong et al., 2021).
To sum up, one can understand a MAL DSL as a collection of
attack trees encoded in assets. These assets can then be combined
by the user to create a representation of the organization’s reality.
In the background, the different attack trees are linked accordingly,
enabling the overall security assessment of the model.
Finally, domain speciﬁc languages devised in MAL also
encode how the attack graphs are generated for spe-
ciﬁc instance models. For Attack steps located on the
same Asset this is straight forward: Computer.Connect can
lead to both Computer.ExploitKnownVulnerability and Com-
puter.ExploitZeroDayVulnerability (depending on Computer.Patched),
and these two Attack steps in turn lead to Com-
puter.Compromise. This attack graph fragment is valid for all
Computers. But, from Computer.Compromise we would normally
think that the attacker would be able to do the Attack step
Transmit on all the Networks that the Computer has a Commu-
nication Link to. And once there, the Attacker can do Com-
puter.Connect on all (other) Computers Linked to the Network.
From such logic a speciﬁc attack graph instance can be derived
for every instance model and the TTC values in the graph can be
aggregated to global TTC values for all the Attack steps, given
an Attacker starting point.
### 3. Related work
We divide the coverage of related work into security model-
ing and analysis approaches on the one hand and formalizations
of modeling languages on the other.
#### 3.1. Security modeling and analysis
Before discussing existing approaches for security modeling and
analysis, we reason about the requirements towards the MAL and
compare it to existing solutions:
1. Causality-based security predictions. The MAL should support
causality-based security predictions, instead of a formal veriﬁ-
cation of the system’s design. The rational behind this require-
ment is to support the analysis of the quality of the later imple-
mentation and conﬁguration vulnerabilities of systems. More-
over, different simulations should be performed considering dif-
ferent defenses effective or not.
2. Enterprise-wide systems-of-systems analysis. The MAL should
be able to simulate enterprise-wide systems-of-systems to pro-
vide an overall security assessment of the entire IT landscape
or sub-sets of it.
3. Individual component analysis. Additionally to the aforemen-
tioned requirement, MAL should also support a more detailed
analysis of individual components. This allows the security an-
alyst to inspect also more details of a certain system if neces-
sary.
4. Enable non-security expert for analysis. The security analysis
of systems is challenging as the analyst needs domain speciﬁc
knowledge as well as security knowledge. At the same time, the
pool of persons having knowledge in both areas is restricted.
To address this challenge, MAL should also enable non-security
experts to perform the analysis.
The ﬁeld of model-driven security engineering includes quite
a large number of DSLs, such as UMLsec (Jürjens, 2002; 2005),
SecureUML (Basin et al., 2011; 2006), SECTET (Alam et al., 2007;
Hafner et al., 2006), or STS-ml (Paja et al., 2015). In these lan-
guages it is possible to specify a system design in terms of compo-
nents and interactions between them. Additionally, security prop-
erties such as constraints, requirements, or threats can be deﬁned.
Security analysis is then conducted using model checking and by
searching for constraint violations, while different languages use
different formalisms to build up their syntax and semantics.
The approach of these DSLs promotes secure system design or
in other words a formal veriﬁcation of the system. While it is ben-
eﬁciary to have such a formal veriﬁcation, these DSLs struggle to
easily simulate different conﬁgurations of the system, i.e., differ-
ent vulnerabilities and defenses in place. This can be accomplished
by MAL. Moreover, are these solutions not domain-speciﬁc in the
sense that they are designed for a certain business domain, such
as power or health. Instead, they are general purpose languages
that require already the respective security knowledge to be used
effectively.
Moreover, these languages are classically designed to either an-
alyze an organization more holistically or solely provide means to
2

## Page 3

W. Wideł, S. Hacks, M. Ekstedt et al. Computers & Security 130 (2023) 103284
analyze single components such as a single application. Other se-
curity languages solely focus on the modeling of security, such as
CORAS (Lund et al., 2010), secureTROPOS (Mouratidis et al., 2002),
and SecDSVL (Almorsy and Grundy, 2014). These languages capture
security properties but do not provide any reasoning logic to ana-
lyze models.
Another well-established language for modeling security is at-
tack trees, attributed to Bruce Schneier (Schneier, 1999; 2000),
and closely related to threat logic trees (Weiss, 1991). Formal
foundations of attack trees have been laid by Mauw and Oost-
dijk (2005), and the framework was extended to include defenses
by Kordy et al. (2010). Since then, many attack-tree-based ap-
proaches have been presented (Ingols et al., 2009; Kotenko and
Doynikova, 2014; Ou and Singhal, 2011; Williams et al., 2008).
Kordy et al. (2014) provide a summary on those approaches, and
an overview of the recent advances in attack tree-based modeling
of security is given in Widełet al. (2019). Among these advances
are (Ivanova et al., 2015; Pinchinat et al., 2014; Vigo et al., 2014),
which tackle the issue of semiautomatic generation of attack trees
from models of systems of interest.
Attack trees allow the security assessment on a detail level of
choice and can be also easily altered to allow the analysis of dif-
ferent system conﬁgurations. However, they require a high level of
understanding of the concept itself and are no tool that can be pro-
vided to non-security experts to analyze their systems.
In each of these works, the burden of describing the attack
logic is put on the creator of the model. In the MAL framework,
the attack logic is encoded in a DSL created by the domain ex-
perts, which we support by a method to design the language it-
self (Hacks et al., 2022) and methods to determine the vulnerabili-
ties’ properties (Rencelj Ling and Ekstedt, 2022; Xiong et al., 2021).
Thus, the modeler needs only to specify the objects in the system
and the relations between them, while ﬁrst research has been con-
ducted to support the automated generation of concrete MAL DSL
instances (Aldea and Hacks, 2022; Hacks et al., 2021; Rencelj Ling
and Ekstedt, 2021). Furthermore, the process of generating attack
graphs from models created using MAL is fully automated by the
tool support (Ekstedt et al., 2015), which takes the model and the
MAL DSL and generates the related attack graph from it.
Apart from research related publications, there exists also a
number of attack graph-based tools. These tools require informa-
tion on existing system or infrastructure and can from this auto-
matically derive attack graphs. The MulVal tool (Homer et al., 2013;
Ou et al., 2005) constructs logical attack graphs by associating the
vulnerabilities extracted from scans. k-defense Safety (Wang et al.,
2014) extends MulVAL for the computation of zero-day attack
graphs. NAVIGATOR (Chu et al., 2010) considers identiﬁed vulnera-
bilities as directly exploitable by the attacker, provided that the lat-
ter has access to the vulnerable system. The TVA tool (Noel et al.,
2009) models networks in terms of security conditions and uses
a database of exploits for specifying transitions between these
security conditions. Similarly, NetSecuritas (Ghosh et al., 2015)
composes scanners output and known exploits to generate attack
graphs and corresponding security recommendations.
Probabilistic attack graph modeling is a research subﬁeld of its
own. Frigault et al. (2008) translate “raw” attack graphs obtained
with the TVA-tool into dynamic Bayesian networks and convert
CVSS scores to probabilities. Similarly, Xie et al. (2010) rely on
CVSS to model uncertainties in the attack structure, attacker’s ac-
tions, and alerts triggering. Poolsappasit et al. (2012) use Bayesian
attack graphs to estimate the security risk on network systems
and produce a security mitigation plan using a genetic algorithm.
In the framework developed by Arnold et al. (2014), the basic ac-
tions in attack trees are assigned probability distributions of time
needed for their execution. While in our setting, values are sam-
pled from such distributions and attack simulations employing
these values are performed in order to approximate the overall
distribution corresponding to compromise of assets of interest, the
goal of Arnold et al. (2014) is to derive the exact distribution for
the main goal of the attacker from those distributions. They fulﬁll
the most of the requirements presented before, while still being
designed for security-experts and as general purpose tools. Thus,
these are also no tools that can be provided to domain experts di-
rectly.
Previous work that has led up to the need to develop MAL in-
cludes CySeMoL (Sommestad et al., 2013), P2CySeMoL (Holm et al.,
2015), and pwnPr3d (Johnson et al., 2016). These are all DSLs that
automatically generate probabilistic attack graphs from a given sys-
tem language speciﬁcation. However, they do not follow an explicit
meta language, making them hard to change and re-use.
#### 3.2. Modeling language formalization
When it comes to the formalization of DSLs much work has
been conducted on deﬁning semantics of UML diagrams, espe-
cially class diagrams. Szlenk (2006) recognized that the semantics
of models written in UML is not precisely deﬁned, which might
lead to incorrect interpretation of models and negatively inﬂu-
ence the veriﬁcation of a model and its transformation. He for-
mally deﬁned the syntax of UML class diagrams and its seman-
tics. Our formalization of MAL is strongly based on his approach.
Costal et al. (2011) took a closer look at the semantics of sub
setting, specialization, and redeﬁnition relations in UML diagrams.
Feinerer and Salzer (2014) deﬁned semantics for multiplicities of
associations. Abdulganiyyi and Ibrahim (2014) developed a seman-
tic abstraction by a logical approach to trace back former rela-
tions in evolved diagrams. Another stream of syntax and seman-
tics in UML diagrams focuses on the deﬁnition of algebra for class
diagrams. For instance, Enjo et al. (2009) present a syntax of a
class diagram describing a data model for syntactical foundation
for class diagram algebra and the related operations.
The endeavors of the scientiﬁc community are not restricted
to the formalization of UML diagrams. There is also a plenty of
research related to the formalization of DSLs. Jackson and Szti-
panovits (2009) develop formal foundations for the structural
semantics DSLs. A higher level of abstraction is presented by
Jiang and Wang (2012) focusing on formalizing meta DSLs. They
propose a formal representation of domain speciﬁc meta model-
ing languages. They use ﬁrst-order logic to verify the consistency
of their language and meta-models built based on the language.
Similarly to our work, Stappers et al. (2012) formalize an al-
ready existing DSL. However, their language supports the deﬁnition
of predictive and reactive rules to optimally allocate manufacturing
activities to mechatronic subsystems over time while subjected to
dynamic constraints. They follow a two steps approach. First, they
project the existing concrete syntax onto a formal abstract syn-
tax that deﬁnes the language operators and process terms. Second,
they deﬁne the dynamic operational semantics using structural op-
erational semantics.
### 4. A MAL example
In this section we provide an example to illustrate the prac-
tical use of MAL. Due to space restrictions the example is small
and does not cover the full semantic scope of MAL. Instead, the
purpose of this section is to illustrate that MAL can be employed
practically for threat modeling using available tools.2
2
All tools used here are available on https://mal-lang.org
3

## Page 4

W. Wideł, S. Hacks, M. Ekstedt et al. Computers & Security 130 (2023) 103284
#### 4.1. An example language
The domain for our example language is basic computer net-
works and it is developed around the defense mechanisms of cre-
dential encryption, software patching, and antivirus software. We
provide two alternative speciﬁcations of the language. The ﬁrst one
is based on the human-readable syntax of MAL, as used by MAL
practitioners and as accepted by existing MAL compilers. The sec-
ond one employs the syntax deﬁned in Section 5.
As a starting point the language deﬁnes Machine, which
is an abstract representation of items that can execute code.
Machine is extended, in several layers, into a number of con-
crete assets; Hardware, Software, OperatingSystem, and
AntiVirus. The speciﬁcation also includes computer Network
and Credentials. In terms of associations, Machine can exe-
cute Software and all Software requires a machine to execute
on. Moreover, Machines can communicate over Networks and
they can store Credentials, and Credentials can allow ac-
cess to Machines.
On the Machine asset, we ﬁrst ﬁnd the attack step connect,
representing the attacker gaining logical access to the Machine
and thus being allowed to send basic requests to it, and the at-
tack step compromise indicating that the attacker has full con-
trol over the Machine. Furthermore, we ﬁnd attack logic for
taking over the Machine by means of using credentials. The
authCompromise attack step is of type AND and requires that
the attacker both have done connect and authenticate. In
order to know how the attacker is able to authenticate we
in turn need to look to the Credentials asset to see that
this is achieved by succeeding by a compromise there, since
this attack steps leads to authenticate on all the Machines
that this Credentials instances provides access to, speciﬁed
by the role authenticates. To compromise Credentials
in turn is achieved by one out of two attack vectors depending
on if the defense mechanism encrypted is true or false. When
encrypted, the attack logic forces the attacker to do the at-
tack step crack, where we also have encoded TTC distribution
for this operation. Logically, the encrypted defense is thus dis-
abling the compromiseUnencrypted attack step since this is an
ANDstep requiring all parents to be true. Analogously to Machine,
the attack vectors on the Credentials cannot be initiated unless
4

## Page 5

W. Wideł, S. Hacks, M. Ekstedt et al. Computers & Security 130 (2023) 103284
Fig. 1. The example model.
the attacker managed to access it. And if we continue tracing
the logic backwards this step is achieved by compromising any
Machine that has a storage association to the Credentials.
The other main chunk of the attack logic is found on the
OperatingSystem. Here, two main attack vectors are encoded,
one is the exploitation of a known vulnerability and the other
is the exploitation of a zero-day vulnerability. Analogously to
the logic found on the credentials, the patched defense dis-
ables the attemptExploitKnownVulnerability step and,
thus, the on-following steps in that vector. The ﬁnal defense
mechanism considered in the example is antivirus. This is en-
coded using the exist and does not exist steps. Intuitively, if
OperatingSystem is executing Software of type AntiVirus,
then the attacker can try to bypass the antivirus. Technically,
this means that in the attack graph corresponding to the model
the node antiVirusProtected will be compromised, and so
the nodes representing bypassAVWithKnownVulnExploit and
bypassAVWithZeroDayExploit steps will be reachable by
the attacker. If there is no AntiVirus being executed by the
OperatingSystem, then this node will not be compromised, and
so the two aforementioned nodes will not be reachable by the at-
tacker.3
Finally, the compromise of a Machine allows that attacker to
communicate on the Networks it is connected to, compromised
Software can connect the Machine it is executed on, in addi-
tion to the attack steps enabled as speciﬁed in Machine.
#### 4.2. An example model
In Fig. 1, a small example model created in the above-described
language is shown. It contains a single network with four comput-
ers on it. In our scenario we consider the computer running the
OperatingSystem WellProtected_OS being the valuable target we
want to protect, and thus the focus of our analysis. The model also
contains a computer assumed to have already been compromised
by the attacker. Moreover, there are two additional computers, one
being patched and the other not being patched, but instead pro-
tected by antivirus. The latter computer contains a database in
3
The reason why we use both exist and does not exist steps here is to both enable
and disable attack vectors. In the case of an unpatched machine, it is still possible
to deploy a zero-day vulnerability exploit, whereas bypassing an antivirus system
cannot be done if it is not present.
which credentials to the target computer are stored. The target op-
erating system is both patched and guarded by antivirus.
In the following sections, we describe the overall syntax and
semantics of MAL. To ease the understanding of MAL, we refer to
this example and use it to illustrate the concrete instantiation.
### 5. The syntax of MAL
Next, we will next present our formalization. Therefore, we will
state ﬁrst the needed preliminaries, followed by the abstract syn-
tax of MAL illustrated by a concrete example based on the previous
section.
#### 5.1. Preliminaries
The set of natural numbers is denoted by N. For a set X, the
powerset of X is denoted by 2X, and the set of all functions from
X to a set Y, by YX. The notation X ⊂ Y means that X is a subset
of Y and X = Y. If f is a function from X ⊆ X to Y, then it is a
partial function from X to Y, denoted f : X  Y; it does not neces-
sarily map every element of X on an element of Y. The domain of
f is denoted by dom(f). For a tuple or a list l, the function πi(l)
returns the ith element of l.
For p ∈ [0,1], we use Bernoulli(p) for the probability distribu-
tion of a random variable that takes value 1 with probability p, and
value 0 with probability 1 − p. Finally, if φ is a probability distribu-
tion such as exponential or gamma, then by x ← φ we mean that
the value of x is obtained by sampling from the distribution φ.
#### 5.2. Abstract syntax
To deﬁne the abstract syntax of MAL, let
• Classifiers be the set of all classiﬁers (asset names),
• Steps denote the set of all the steps that might appear in lan-
guages,
• Roles denote the set of all the roles that might appear in lan-
guages,
• Types denote the set {&,|,#,E,!E} of types of steps,
• F denote the set of all probability distributions.
The types & and | are used for annotating AND attack steps and
OR attack steps, respectively. Intuitively, a step of type & can be ex-
ecuted only if all of its parent steps have been executed. To be able
5

## Page 6

W. Wideł, S. Hacks, M. Ekstedt et al. Computers & Security 130 (2023) 103284
to execute an attack step of type |, the attacker needs to execute
at least one of its parent steps. Steps of type # are defense steps.
These represent security measures that can be implemented in the
system to counter particular attack steps. The last two types sym-
bols, E and !E, stand for exists and does not exist quantiﬁers. The
steps of these types are used for modeling dependencies between
availability of some attack steps to the attacker and the existence
of some assets or lack thereof.
Relations between assets and steps within the assets are de-
scribed with terms generated by the grammar
termr ::= role|(termr ∧ termr)|(termr ∨ termr)
|(termr \termr)|(termr.termr)
|termr[class],
terms ::= step|termr.step,
(1)
with role ∈ Roles,class ∈ Classifiers and step ∈ Steps. The set of
all terms of the form termr and the set of all terms of the form
terms are denoted by Termr and Terms, respectively. The parentship
relation between attack steps and the relation of defense steps
countering attack steps are speciﬁed using the terms in Terms. The
terms in Termr are used for expressing the preconditions for the
steps of types E and !E.
A language expressed with MAL is a tuple
L = (classiﬁersL,assetStepsL,stepSpecL,
endsL,multsL,rolesL,extendsL),
where
1. classiﬁersL is a set of classiﬁers of the language. It can be par-
titioned into sets of assets and associations, denoted by assetsL
and associationsL, respectively. Among the assets, there are ab-
stract assets, the set of which we denote by abstrAssetsL. That
is,
classiﬁersL ⊆ Classifiers,
classiﬁersL = assetsL ∪ associationsL,
assetsL ∩ associationsL = ∅,
abstrAssetsL ⊆ assetsL.
2. assetStepsL is a function assigning to each of the assets in L a
set of steps related to this asset. That is,
assetStepsL : assetsL → 2Steps
.
3. stepSpecL is a function specifying properties of steps in the
context of particular assets: their types, their prerequisites and
consequences, and the probability distributions of their TTCs.
That is,
stepSpecL : assetsL × Steps 
Types × 2Termr
× 2Terms
× F,
and stepSpecL is deﬁned for every pair (asset,step) such that
asset ∈ assetsL and step ∈ assetStepsL(asset).
For an asset asset in assetsL and a step step ∈ assetStepsL(asset),
we let
typeL(asset,step) :=
π1(stepSpecL(asset,step))
to denote the type of step step in the context of the asset asset.
The following is required of stepSpecL: for every asset
asset ∈ assetsL and every step step ∈ assetStepsL(asset) satisfy-
ing stepSpecL(asset,step) = (t,R,S, f), it must hold that
• if step ∈ S, then
step ∈ assetStepsL(asset), and
typeL(asset,step) ∈ {&,|},
• if t ∈ {&,|,#}, then R = ∅,
• if t ∈ {E,!E}, then R = ∅.
Intuitively, the ﬁrst of the above requirements states that if
there is a relation between two steps (i.e., step is a parent at-
tack step of an attack step step, or step is a defense step coun-
tering an attack step step) that does not exploit any associa-
tions between assets, then both these steps are related to the
same asset. The remaining two provide a distinction between
the exists and does not exist steps and the other steps. Theses
two steps specify conditions under which some other steps are
available for the attacker to execute, the conditions being the
presence or lack of some instances of assets. Such instances are
speciﬁed using terms in Termr, stored in the set R. Thus, the
set R is required to be non-empty for these two steps, and to
be empty for the other steps.
4. endsL is a function specifying for a given association the assets
related to each other through the association. That is,
endsL : associationsL → assetsL × assetsL.
5. multsL is a function specifying multiplicities of association ends,
i.e., the possible numbers of assets instances in association in-
stances. It does so by assigning to each of the associations a
pair of non-empty sets of natural numbers. That is,
multsL : associationsL →
(2N\{0} \{∅})× (2N\{0} \{∅}).
6. rolesL is a labeling function specifying the roles of the assets in
associations:
rolesL : associationsL → Roles × Roles.
7. extendsL describes the extension relation: if an asset is an ex-
tension of another asset, then it is mapped by extendsL to the
latter. If an asset extends another asset, then it inherits all steps
of the latter, together with their types. The remaining proper-
ties of the steps might be different. That is,
L.extendsL : assetsL  assetsL,
for every asset ∈ dom(extendsL) it holds that
assetStepsL(asset) ⊇
assetStepsL(extendsL(asset)),
and for every step ∈ assetStepsL(extendsL(asset)) it holds that
typeL(asset,step) =
typeL(extendsL(asset),step).
Furthermore, intuitively speaking, the extending asset partici-
pates in all associations in which the extended asset partic-
ipates, i.e., for every asset ∈ dom(extendsL) and every assoc ∈
associationsL satisfying
extendsL(asset) = πi(endsL(assoc))
for some i ∈ {1,2}, there is an association assoc ∈ associationsL
such that
multsL(assoc) = multsL(assoc),
rolesL(assoc) = rolesL(assoc),
πi(endsL(assoc)) = asset,
πj(endsL(assoc)) = πj(endsL(assoc)),
with j satisfying {i, j} = {1,2}.
6

## Page 7

W. Wideł, S. Hacks, M. Ekstedt et al. Computers & Security 130 (2023) 103284
Finally, none of the assets can be an extension of itself (neither
direct nor indirect). Formally, for every asset ∈ assetsL and every
n ∈ N, n = 0, it must hold that
extends
n
L (asset) = asset.
Example language
For a description employing our formal syntax, let
L = (classiﬁersL,assetStepsL,stepSpecL,
endsL,multsL,rolesL,extendsL)
be the language presented above. The classiﬁers of the language L
are
classiﬁersL = assetsL ∪ associationsL,
with
assetsL = {Machine,Hardware,Software,
OperatingSystem,AntiVirus,Network,
Credentials},
abstrAssetsL = {Machine}, and
associationsL = {Execution,Communication,
Storage,Access}.
The extendsL function is deﬁned as
extendsL(Hardware) = Machine,
extendsL(Software) = Machine,
extendsL(OperatingSystem) = Software,
extendsL(AntiVirus) = Software.
We will not give the full description of the remaining compo-
nents of L, but instead provide examples illustrating how this de-
scription can be derived from the human-readable one.
Generally, steps related to a particular asset are listed within
the curly brackets following the asset’s name, in the lines starting
with one of the type symbols &,|,#,E,!E. For instance,
assetStepsL(Machine) = {connect,authenticate,
authCompromise,compromise}.
In the case of assets extending other assets, the steps having
exactly the same properties as in the context of the extended
asset are not listed. For example, there are no steps present in
the description of the Hardware asset. Since Hardware extends
Machine, this fact should be interpreted as
assetStepsL(Hardware) = assetStepsL(Machine).
The lines starting with arrows contain the prerequisites (<-;
only for the exists and does not exist steps) and the consequences
(->) of steps. The special arrow +> is used for listing additional
consequences that a step has in the context of the asset, but not
in the context of the parent asset. The probability distributions of
steps in the context of particular assets are speciﬁed within square
brackets; if a distribution is not stated explicitly, then it is assumed
that the execution of the step is instantaneous, and so its TTC dis-
tribution is Bernoulli(0). For instance,
stepSpecL(Software,compromise) =
(|,∅,{executees.connect,
storedCreds.access,
networks.communicate,
executor.connect},Bernoulli(0)),
stepSpecL(OperatingSystem,antiVirusProtected) =
(E,{executees[AntiVirus]},
{bypassAVwithKnownVulnerability,
bypassAVwithZeroDayExploit},Bernoulli(0)).
The properties of associations are listed in the block at the end.
The asterisk means that any non-zero number of assets of particu-
lar type can participate in the association. In other words, the sym-
bol ∗
represents the set N \{0}. Hence, the formal description of
the Execution association is
endsL(Execution) = (Machine,Software),
multsL(Execution) = ({1},N \{0}),
rolesL(Execution) = (executor,executees),
and the formal speciﬁcation of the remaining associations can be
derived analogously.
### 6. The semantics of MAL
The syntax given in the previous section describes the structure
of DSLs created using MAL. In this section, we focus on models that
can be expressed using such DSLs, and we deﬁne a procedure for
automatic transformation of these models into attack graphs.
#### 6.1. Model
The existing instances of a classiﬁer are called its extent. If we
let Instances denote the set of possible instances of classiﬁers,
then a model M can be seen as a tuple
M = (instancesM,endsM,entryPointsM,defensesM),
where
1. instancesM is a partial function that maps classiﬁers to their
extents (intuitively, it speciﬁes which of the instances present
in the model are instantiations of which classiﬁers). That is,
instancesM : Classifiers  2Instances
.
2. endsM is a function that maps each of the instances of asso-
ciations (links) to a pair of sets of instances of assets (objects)
connected by the link. That is,
endsM :Instances 
2Instances
× 2Instances
.
3. entryPointsM is a set of pairs (instance,step) ∈ instancesM ×
Steps representing attack steps known to have been already ex-
ecuted by the attacker.
4. defensesM is a function
defensesM : instancesM × Steps  F
assigning to each of the defense steps present in the model
a Bernoulli probability distribution describing the likelihood of
the defense being implemented.
#### 6.2. Model respecting a DSL
If we let Languages and Models denote the set of all languages
as deﬁned in Section 5 and the set of all models as deﬁned in
Section 6.1, respectively, then for a given language L ∈ Languages
and a model M ∈ Models we say that M respects L, denoted
Resp(L,M),
if and only if:
7

## Page 8

W. Wideł, S. Hacks, M. Ekstedt et al. Computers & Security 130 (2023) 103284
1. M contains instantiations of classiﬁers of L, and no others. That
is,
dom(instancesM) ⊆ classiﬁersL.
2. An instance of a given association respects the speciﬁca-
tion of this association, i.e., it connects the correct num-
bers of instances of assets appearing in this association. That
is, for every association assoc ∈ associationsL, every link link ∈
instancesM(assoc) and for i ∈ {1,2} it holds that
|πi(endsM(link))| ∈ πi(multsL(assoc))
and
πi(endsM(link)) ⊆
instancesM(πi(endsL(assoc))).
3. The extent of an association contains at most one link connect-
ing a given pair of sets of assets instances. That is, for every as-
sociation assoc ∈ associationsL and every two links link1,link2 ∈
instancesM(assoc) satisfying link1 = link2 it holds that
π1(endsM(link1)) = π1(endsM(link2))
or
π2(endsM(link1)) = π2(endsM(link2)).
4. An instance of an asset that extends another asset is also
an instance of the latter. That is, if asset = extendsL(asset),
with asset,asset ∈ assetsL, it holds that instancesM(asset) ⊆
instancesM(asset).
5. Every instance of an abstract asset in the model M is also
an instance of a non-abstract asset extending the former. That
is, for every abstract asset abstrAsset ∈ abstrAssetsL and ev-
ery instance instance ∈ instancesM(abstrAsset) there is an asset
asset ∈ assetsL and a number n ∈ N, n > 0, such that
extends
n
L (asset) = abstrAsset,
instance ∈ instancesM(asset).
6. Every entry point describes an attack step that can
be performed in the modeled infrastructure. That is,
if (instance,step) ∈ entryPointsM, then there is an as-
set asset ∈ assetsL such that instance ∈ instancesM(asset),
step ∈ assetStepsL(asset) and type(asset,step) ∈ {&,|}.
7. The defensesM function assigns a Bernoulli probability distribu-
tion to each of the defense steps related to assets instantiated
in the model, i.e.,
dom(defensesM) =
{(instance,step) : there is asset ∈ assetsL
and step ∈ assetStepsL(asset) such that
instance ∈ instancesM(asset) and
type(asset,step) = #},
and for every (instance,step) ∈ dom(defensesM) it holds that
defensesM((instance,step)) ∈
{Bernoulli(p) : p ∈ [0,1]}.
Example model The speciﬁcation of the model employing the
notation previously introduced can be easily derived from the
above description and from Fig. 1. Denoting the model by M, we
have for example
instancesM(Hardware) = {HW1, HW2, HW3, HW4}
and
entryPointsM = {(Compromised_OS,compromise)}.
The fact that some defenses are functional and others are not, is
modeled by assigning to the defenses appropriate Bernoulli proba-
bility distributions. For instance,
defensesM(Patched_OS,patched) = Bernoulli(1),
defensesM(NotPatched_OS,patched) = Bernoulli(0).
#### 6.3. Evaluation of terms for models
Terms generated using the grammar (1) that appear in a DSL
provide a general description of relations between assets and steps
related to assets. In the context of a speciﬁc model, this description
will be translated into direct relations between particular instances
of assets and particular steps. The functions that will be used for
performing such translation rely on the intuitively obvious notion
of an instance playing a role in a link.
Deﬁnition 1. Let L ∈ Languages be a language, let M be a model
respecting L and let role ∈ Roles. For an instance instance ∈
instancesM(asset) of an asset asset ∈ assetsL and an instance link ∈
instancesM(assoc) of an association assoc ∈ associationsL, we say
that instance plays role role in link if there is i ∈ {1,2} such that
πi(rolesL(assoc)) = role and instance ∈ πi(endsM(link)).
For an instance of an asset and a term termr ∈ Termr, the ob-
jects reachable from the instance in a particular model via links
speciﬁed by termr are determined using the function
evalR :Languages × Models × Instances × Termr
→ Instances
deﬁned recursively in Table 1. For determining steps within such
reachable objects that a step belonging to the instance leads to,
the function
evalS :Languages × Models × Instances
× Steps × Terms
→ Instances,
deﬁned in Table 2 is used.
#### 6.4. Semantics
The semantics deﬁned in this section assigns a function de-
scribing transformation of models speciﬁed with a MAL-created
DSL into attack graphs. By an attack graph, we mean a tuple
(V,A,type,ttc), where V is a set of nodes, A ⊆ V ×V is a set of arcs,
and type : V → {|,&,#} and ttc : V → F are functions associating
nodes with their types and probability distributions, respectively.
Let AG denote the set of all attack graphs.
For a language L ∈ Languages, let fL be the function mapping
models respecting L on attack graphs, i.e.,
fL : {M ∈ Models : Resp(L,M)} → AG,
deﬁned as follows. For a model M respecting L, the image fL(M)
of M by fL is the attack graph (V1 ∪V2,A,type,ttc) deﬁned by
V1 ={(instance,step) : there is asset ∈ assetsL s.t.
instance ∈ instancesM(asset),
step ∈ stepsL(asset)
and typeL(asset,step) ∈ {|,&,#}},
V2 ={(instance,step) : there is asset ∈ assetsL st
instance ∈ instancesM(asset),
step ∈ stepsL(asset),
8

## Page 9

W. Wideł, S. Hacks, M. Ekstedt et al. Computers & Security 130 (2023) 103284
Table 1
Evaluation rules for terms belonging to Termr.
evalR(L,M,instance,role) = {instance : there is assoc ∈ associationsL and
link ∈ instancesM(assoc) such that
instance plays role role in link and
instance plays the other role in link}
evalR(L,M,instance,(term1 ∧ term2)) =evalR(L,M,instance,term1)∩ evalR(L,M,instance,term2)
evalR(L,M,instance,(term1 ∨ term2)) =evalR(L,M,instance,term1)∪ evalR(L,M,instance,term2)
evalR(L,M,instance,(term1 \term2)) = evalR(L,M,instance,term1)\evalR(L,M,instance,term2)
evalR(L,M,instance,(term1.term2)) =

instance∈evalR(L,M,instance,term1 )
evalR(L,M,instance,term2)
evalR(L,M,instance,termr[class]) = evalR(L,M,instance,termr)∩ instancesM(class)
Table 2
Evaluation rules for terms belonging to Terms.
evalS(L,M,instance,step1,step2) = {(instance,step2)}
evalS(L,M,instance,step1,termr.step2) = {(instance,step2) :
instance ∈ evalR(L,M,instance,termr)
and step2 ∈ stepsL(asset) for every
asset such that instance ∈ instancesM(asset)}
typeL(asset,step) = E, and there is
termr ∈ π2(stepSpecL(asset,step)) such that
evalR(L,M,instance,termr) = ∅}
∪
{(instance,step) : there is asset ∈ assetsL st
instance ∈ instancesM(asset),
step ∈ stepsL(asset),
typeL(asset,step) =!E, and there is
termr ∈ π2(stepSpecL(asset,step)) such that
evalR(L,M,instance,termr) = ∅},
A ={

(instance,step),(instance,step)

∈ V ×V :
there is asset ∈ assetsL such that
instance ∈ instancesM(asset) and
step ∈ stepsL(asset),
and there is terms ∈ π3(stepSpecL(asset,step))
such that
(instance,step) ∈
evalS(L,M,instance,step,terms)},
type((instance,step)) =

typeL(asset,step), if instance ∈ instancesM(asset)
and (instance,step) ∈ V1,
&, otherwise,
and
ttc((instance,step)) = π4(stepSpecL(asset,step)),
where asset in the last formula is the unique asset such that
instance ∈ instancesM(asset) and instance / ∈ instancesM(asset) for
every asset ∈ assetsL satisfying extends
n
L (asset) = asset for some
n ∈ N.
The semantics of a language L ∈ Languages is deﬁned as
[[L]] := fL.
### 7. An application of the MAL semantics for security analysis
The MAL semantics deﬁned in the previous section transforms
a MAL model into an attack graph describing the possible behav-
ior of the attacker in the modeled infrastructure. For the purpose
of security analysis various methods can be applied to the attack
graphs, representing different types of attacker behavior. We could
for instance imagine a rational attacker choosing the overall short-
est path, or one that chooses the cheapest next step, or just at-
tacking at random. Although, the goal of this work is to provide
formal foundations for generating attack graphs from MAL-based
DSLs rather than the attack graphs per se are used for quantita-
tive security analysis, we brieﬂy sketch one such method here. This
section describes an implementation found in the MAL tooling4 as
of the date of writing, but the objective of this section is merely
to hint towards the possibilities of MAL-based attack graphs rather
than to develop a full-ﬂedged security analysis framework.
The attack simulation method considered here consists of four
stages. In the ﬁrst of them, it is established which of the defense
measures are in place. This is done by sampling from the defense
steps’ Bernoulli distributions. In the second stage, this knowledge
is combined with the information on the attack steps already per-
formed by the attacker (with some of them speciﬁed explicitly in
the model as the entry points, and others derived from the precon-
ditions of E and !E steps), and used for determining attack steps
reachable by the attacker. For such steps, TTC values are sampled
from their corresponding probability distributions. Finally, these
values are propagated throughout the attack graph, yielding the
overall time needed for compromising particular assets.
Formally, this method can be described as follows: Let L ∈
Languages be a language, let M be a model respecting L and
let(V1 ∪V2,A,type,ttc) = [[L]](M) be the attack graph representing
security scenario modeled with M. To reason conveniently about
the possible defenses against an attack step, we set
Defs(v) = {v ∈ V1 : (v,v) ∈ A,type(v) = #},
for v ∈ V1 satisfying type(v) ∈ {|,&}.
For describing which of the defenses are implemented, deﬁne
the function
imp : {v ∈ V1 : type(v) = #} → {0,1}
by setting imp(v) ← defensesM(v).
Finally, we say that nodes in entryPointsM ∪V2 are the compro-
mised nodes.
A node v ∈ V1 satisfying type(v) ∈ {|,&} is reachable by the at-
tacker if it satisﬁes all of the following conditions.
1. There is a path from at least one of the compromised nodes to
v.
4
Avialable at https://mal-lang.org.
9

## Page 10

W. Wideł, S. Hacks, M. Ekstedt et al. Computers & Security 130 (2023) 103284
2. None of the defenses attached to v is implemented, i.e.,
imp(v) = 0 for every v ∈ Defs(v).
3. If type(v) = &, then every parent of v is reachable by the at-
tacker.
4. If type(v) = |, then at least one of the parents of v is reachable
by the attacker.
For a node v reachable by the attacker, we use Tloc(v) and
Tglob(v) to denote the local and the global time to compromise,
respectively. Furthermore, the parents of v that are reachable by
the attacker are denoted by Parents(v). The values of the local time
to compromise are obtained by setting
Tloc(v) =

0, if v ∈ entryPointsM ∪V2,
← ttc(v) otherwise.
The global time to compromise, that is, an estimate of a time
needed by the attacker for execution of a particular step and all
of its prerequisites, is computed as
Tglob(v) = Tloc(v)+ min
v∈Parents(v)
Tglob(v),
if type(v) = |, and as
Tglob(v) = Tloc(v)+ max
v∈Parents(v)
Tglob(v),
if type(v) = &.
The motivation behind the choice of operations for global time
to compromise computations is as follows. Execution of an attack
step takes time equal to the step’s local time to compromise. In
the case of an OR attack step, its execution requires also executing
at least one of its parents, and in the case of an ANDstep – all of
the parents. Thus, the minimal of the global times to compromise
of the parents is added in computations for an OR node, and the
maximal – in computations for an ANDnode.5
There are many different ways to calculate the TTC based on
preferences for a certain way to for example calculate the shortest
path between the attack surface and the target for which the TTC
should be calculated. All these different calculations adhere still to
the here described semantics of MAL. Accordingly, we do not want
to restrain concrete implementations of MAL to a certain imple-
mentation how to calculate or use the generated attack graph.
Example for time to compromise Using existing tools, which
transform MAL models into attack graphs and use the algorithm
sketched in Section 7 for computing global TTC values, we ob-
tained the optimal attack vector depicted in Fig. 2. In the ﬁgure, we
see that the attacker from the Network can Connect to the WellPro-
tected_OS and the NotPatched_OS. On the latter they are exploiting
a known vulnerability, as the OS is not patched. From there, the
Database is compromised since its credentials is directly accessible
on the OS. In the database, the encrypted credentials to the Well-
Protected_OS are found, and then Cracked. With both a Connection
and the Compromised credentials, the attacker is ﬁnally able to
Compromise the WellProtected_OS by means of authentication. In
Fig. 3, the empirical cumulative distribution function of the global
TTC for the target is plotted. It has been derived from results of a
hundred runs of the algorithm presented in Section 7, employing
the local TTC distributions speciﬁed in the language.
### 8. Conclusions
In this article, we have presented a formal syntax and seman-
tics of the Meta Attack Language (MAL). As with other domain spe-
5
Should all the parents of each of the ANDattack steps be independent, one could
consider taking the sum of their times to compromise instead of the maximal value.
In practice, however, such independence cannot be guaranteed, and the obtained
result would be a potentially hazardous overestimate of the actual time to compro-
mise.
Fig. 2. The shortest attack vector to the target operating system.
Fig. 3. The cumulative distribution function of the global TTC for the target attack
step Compromise on the asset WellProtected_OS.
ciﬁc languages, MAL enables security engineers and researchers to
develop languages that realize many advantages as compared to
other more open and general-purpose approaches. With a tailored
semantic space, it is easier for language developers to understand,
develop, validate, and maintain their work. The same also applies
to the security engineers using the languages. Of course, just like
most software development this requires good coding discipline
from the developers and users with documentation of e.g., design
decisions and overall working of the encoded logic.
Within the security domain, MAL also enables language devel-
opers to both take on a top-down approach with coarsely deﬁned
assets and attack steps that (likely) includes plenty of probabilis-
tic time to compromise distributions with high uncertainties (as
the example in this paper), as well as a bottom-up approach with
a narrower domain but more determinism stemming from logical
necessities in the system conﬁgurations.
This article provides no evaluation of the proposed formalisms.
However, MAL has proven itself as useful in several occasions as
manifested in MAL DSLs for different domains such as general
10

## Page 11

W. Wideł, S. Hacks, M. Ekstedt et al. Computers & Security 130 (2023) 103284
IT (Katsikeas et al., 2020), power (Hacks et al., 2020; Rencelj Ling
and Ekstedt, 2021), or vehicles (Katsikeas et al., 2022). Addition-
ally, MAL was successfully facilitated in different projects like En-
ergyShield6 or SOCCRATES7.
Declaration of Competing Interest
The authors declare that they have no known competing ﬁnan-
cial interests or personal relationships that could have appeared to
inﬂuence the work reported in this paper.
### CRediT authorship contribution statement
Wojciech Wideł: Conceptualization, Methodology, Writing –
original draft. Simon Hacks: Conceptualization, Methodology,
Writing – original draft, Writing – review & editing. Mathias Ekst-
edt: Conceptualization, Methodology, Supervision, Funding acquisi-
tion, Writing – original draft. Pontus Johnson: Conceptualization,
Funding acquisition. Robert Lagerström: Conceptualization, Fund-
ing acquisition.
### Data availability
Data will be made available on request.
### Acknowledgments
This work has received funding from the Swedish Civil Contin-
gencies Agency through the research centre Resilient Information
and Control Systems (RICS), European Union’s H2020 research and
innovation programme under the Grant Agreements no. 833481
and no. 832907, and the Swedish Governmental Agency for Inno-
vation Systems (Vinnova).
### References
Abdulganiyyi, N., Ibrahim, N., 2014. Semantic abstraction of class diagram using log-
ical approach. In: 2014 4th World Congress on Information and Communication
Technologies (WICT 2014), pp. 251–256. doi:10.1109/WICT.2014.7077274.
Alam, M., Breu, R., Hafner, M., 2007. Model-driven security engineering for trust
management in SECTET. JSW 2 (1), 47–59.
Aldea, A., Hacks, S., 2022. Analyzing enterprise architecture models by means of the
meta attack language. In: Advanced Information Systems Engineering: 34th In-
ternational Conference, CAiSE 2022, Proceedings. Springer, pp. 423–439. Leuven,
Belgium, June 6–10
Almorsy, M., Grundy, J., 2014. SecDSVL: a domain-speciﬁc visual language to support
enterprise security modelling. In: Software Engineering Conference (ASWEC).
IEEE, pp. 152–161. 2014 23rd Australian
Arnold, F., Hermanns, H., Pulungan, R., Stoelinga, M., 2014. Time-dependent analysis
of attacks. In: Principles of Security and Trust - Third International Conference,
POST 2014, Held as Part of the European Joint Conferences on Theory and Prac-
tice of Software, ETAPS 2014, Proceedings, pp. 285–305. Grenoble, France, April
5–13
Basin, D., Clavel, M., Egea, M., 2011. A decade of model-driven security. In: Proceed-
ings of the 16th ACM Symposium on Access Control Models and Technologies.
ACM, pp. 1–10.
Basin, D., Doser, J., Lodderstedt, T., 2006. Model driven security: from UML models
to access control infrastructures. ACM Trans. Softw. Eng. Methodol. (TOSEM) 15
(1), 39–91.
Chu, M., Ingols, K., Lippmann, R., Webster, S., Boyer, S., 2010. Visualizing attack
graphs, reachability, and trust relationships with NAVIGATOR. In: Proc. of the
7th Int. Symp. on Visualization for Cyber Security. ACM, pp. 22–33.
Costal, D., Gómez, C., Guizzardi, G., 2011. Formal semantics and ontological analysis
for understanding subsetting, specialization and redeﬁnition of associations in
UML. In: Jeusfeld, M., Delcambre, L., Ling, T.-W. (Eds.), Conceptual Modeling –
ER 2011. Springer Berlin Heidelberg, Berlin, Heidelberg, pp. 189–203.
Ekstedt, M., Johnson, P., Lagerström, R., Gorton, D., Nydrén, J., Shahzad, K., 2015. se-
curiCAD by foreseeti: a CAD tool for enterprise cyber security management. In:
Enterprise Distributed Object Computing Workshop (EDOCW), 2015 IEEE 19th
International. IEEE, pp. 152–155.
Enjo, H., Tanabu, M., Iijima, J., 2009. A step toward foundation of class diagram alge-
bra for enterprise service systems. In: 2009 6th International Conference on Ser-
vice Systems and Service Management, pp. 456–460. doi:10.1109/ICSSSM.2009.
5174926.
6
https://energy-shield.eu/
7
https://www.soccrates.eu/
Feinerer, I., Salzer, G., 2014. Numeric semantics of class diagrams with multiplicity
and uniqueness constraints. Softw. Syst. Model. 13 (3), 1167–1187. doi:10.1007/
s10270-012-0294-4.
Frigault, M., Wang, L., Singhal, A., Jajodia, S., 2008. Measuring network security us-
ing dynamic Bayesian network. In: Proc. of the 4th ACM Workshop on Quality
of Protection. ACM, pp. 23–30.
Ghosh, N., Chokshi, I., Sarkar, M., Ghosh, S.K., Kaushik, A.K., Das, S.K., 2015. NetSecu-
ritas: an integrated attack graph-based security assessment tool for enterprise
networks. In: Proc. of the 2015 Int. Conf. on Distributed Computing and Net-
working. ACM, p. 30.
Hacks, S., Katsikeas, S., 2021. Towards an ecosystem of domain speciﬁc languages for
threat modeling. In: International Conference on Advanced Information Systems
Engineering. Springer, pp. 3–18.
Hacks, S., Katsikeas, S., Ling, E., Lagerström, R., Ekstedt, M., 2020. PowerLang: a
probabilistic attack simulation language for the power domain. Energy Inf. 3
(1), 1–17.
Hacks, S., Katsikeas, S., Rencelj Ling, E., Xiong, W., Pfeiffer, J., Wortmann, A., 2022.
Towards a systematic method for developing meta attack language instances.
In: Enterprise, Business-Process and Information Systems Modeling: 23rd Inter-
national Conference, BPMDS 2022 and 27th International Conference, EMMSAD
2022, Held at CAiSE 2022, Proceedings. Springer, pp. 139–154. Leuven, Belgium,
June 6–7, 2022
Hacks, S., Lagerström, R., Ritter, D., 2021. Towards automated attack simulations of
BPMN-based processes. In: 2021 IEEE 25th International Enterprise Distributed
Object Computing Conference (EDOC). IEEE, pp. 182–191.
Hacks, S., Persson, L., Hersén, N., 2023. Measuring and achieving test coverage of
attack simulations extended version. Softw. Syst. Model. 22 (1), 31–46.
Hafner, M., Breu, R., Agreiter, B., Nowak, A., 2006. SECTET: An extensible framework
for the realization of secure inter-organizational workﬂows. Internet Res. 16 (5),
491–506.
Holm, H., Shahzad, K., Buschle, M., Ekstedt, M., 2015. P2
CySeMoL: predictive, proba-
bilistic cyber security modeling language. IEEE Trans. Dependable Secure. Com-
put. 12 (6), 626–639. doi:10.1109/TDSC.2014.2382574.
Homer, J., Zhang, S., Ou, X., Schmidt, D., Du, Y., Rajagopalan, S.R., Singhal, A., 2013.
Aggregating vulnerability metrics in enterprise networks using attack graphs. J.
Comput. Secur. 21 (4), 561–597.
Ingols, K., Chu, M., Lippmann, R., Webster, S., Boyer, S., 2009. Modeling modern net-
work attacks and countermeasures using attack graphs. In: Computer Security
Applications Conference, 2009. ACSAC’09. Annual. IEEE, pp. 117–126.
Ivanova, M.G., Probst, C.W., Hansen, R.R., Kammüller, F., 2015. Transforming graphi-
cal system models to graphical attack models. In: Graphical Models for Security
- Second International Workshop, GraMSec 2015, pp. 82–96. Verona, Italy, July
13, 2015, Revised Selected Papers
Jackson, E., Sztipanovits, J., 2009. Formalizing the structural semantics of domain-
speciﬁc modeling languages. Softw. Syst. Model. 8 (4), 451–478. doi:10.1007/
s10270-008-0105-0.
Jiang, T., Wang, X., 2012. Formalizing domain-speciﬁc metamodeling language
XMML based on ﬁrst-order logic. J. Softw. 7 (6). doi:10.4304/jsw.7.6.1321-1328.
Johnson, P., Lagerström, R., Ekstedt, M., 2018. A meta language for threat model-
ing and attack simulations. In: Proceedings of the 13th International Conference
on Availability, Reliability and Security. ACM, New York, NY, USA doi:10.1145/
3230833.3232799.
Johnson, P., Vernotte, A., Ekstedt, M., Lagerström, R., 2016. pwnPr3d: an attack–
graph-driven probabilistic threat-modeling approach. In: Availability, Reliability
and Security (ARES), 2016 11th International Conference on. IEEE, pp. 278–283.
Jürjens, J., 2002. UMLsec: extending UML for secure systems development. In: Inter-
national Conference on The Uniﬁed Modeling Language. Springer, pp. 412–425.
Jürjens, J., 2005. Secure Systems Development with UML. Springer Science & Busi-
ness Media.
Katsikeas, S., Hacks, S., Johnson, P., Ekstedt, M., Lagerström, R., Jacobsson, J., Wällst-
edt, M., Eliasson, P., 2020. An attack simulation language for the it domain. In:
International Workshop on Graphical Models for Security. Springer, pp. 67–86.
Katsikeas, S., Johnson, P., Hacks, S., Lagerström, R., 2019. Probabilistic modeling and
simulation of vehicular cyber attacks: an application of the meta attack lan-
guage. In: Proceedings of the 5th International Conference on Information Sys-
tems Security and Privacy.
Katsikeas, S., Johnsson, P., Hacks, S., Lagerström, R., 2022. VehicleLang: a proba-
bilistic modeling and simulation language for modern vehicle IT infrastructures.
Comput. Secur. 117, 102705.
Kordy, B., Mauw, S., Radomirović, S., Schweitzer, P., 2010. Foundations of attack–de-
fense trees. In: International Workshop on Formal Aspects in Security and Trust.
Springer, pp. 80–95.
Kordy, B., Piètre-Cambacédès, L., Schweitzer, P., 2014. DAG-based attack and defense
modeling: don’t miss the forest for the attack trees. Comput. Sci. Rev. 13, 1–38.
Kotenko, I., Doynikova, E., 2014. Evaluation of computer network security based on
attack graphs and security event processing. J. Wirel. Mob. Netw. Ubiquitous
Comput. Dependable Appl. (JoWUA) 5 (3), 14–29.
Lund, M.S., Solhaug, B., Stølen, K., 2010. Model-Driven Risk Analysis: The CORAS Ap-
proach. Springer Science & Business Media.
Mauw, S., Oostdijk, M., 2005. Foundations of attack trees. In: International Confer-
ence on Information Security and Cryptology. Springer, pp. 186–198.
Mouratidis, H., Giorgini, P., Manson, G., Philp, I., et al., 2002. A natural extension
of tropos methodology for modelling security. In: Proceedings Agent Oriented
Methodologies Workshop, Annual ACM Conference on Object Oriented Program-
ming, Systems, Languages (OOPSLA). Citeseer. Seattle-USA
11

## Page 12

W. Wideł, S. Hacks, M. Ekstedt et al. Computers & Security 130 (2023) 103284
Noel, S., Elder, M., Jajodia, S., Kalapa, P., O’Hare, S., Prole, K., 2009. Advances in
topological vulnerability analysis. In: Conference For Homeland Security, 2009.
CATCH ’09. Cybersecurity Applications Technology, pp. 124–129. doi:10.1109/
CATCH.2009.19.
Ou, X., Govindavajhala, S., Appel, A.W., 2005. MulVAL: a logic-based network secu-
rity analyzer. USENIX Security.
Ou, X., Singhal, A., 2011. Attack graph techniques. Quant. Secur. Risk Assess. Enter-
prise Netw. doi:10.1007/978-1-4614-1860-3_2.
Paja, E., Dalpiaz, F., Giorgini, P., 2015. Modelling and reasoning about security re-
quirements in socio-technical systems. Data Knowl. Eng. 98, 123–143.
Pinchinat, S., Acher, M., Vojtisek, D., 2014. Towards synthesis of attack trees for
supporting computer-aided risk analysis. In: Software Engineering and Formal
Methods - SEFM 2014 Collocated Workshops: HOFM, SAFOME, OpenCert, MoK-
MaSD, WS-FMDS, pp. 363–375. Grenoble, France, September 1–2, 2014, Revised
Selected Papers
Poolsappasit, N., Dewri, R., Ray, I., 2012. Dynamic security risk management using
Bayesian attack graphs. IEEE Trans. Dependable Secure Comput. 9 (1), 61–74.
doi:10.1109/TDSC.2011.34.
Rencelj Ling, E., Ekstedt, M., 2021. Generating threat models and attack graphs based
on the IEC 61850 system conﬁguration description language. In: Proceedings of
the 2021 ACM Workshop on Secure and Trustworthy Cyber-Physical Systems,
pp. 98–103.
Rencelj Ling, E., Ekstedt, M., 2022. Estimating the time-to-compromise of exploiting
industrial control system vulnerabilities. In: 8th International Conference on In-
formation Systems Security and Privacy-ICISSP, Vol. 1, pp. 96–107.
Schneier, B., 1999. Attack trees. Dr. Dobb’s J. 24 (12), 21–29.
Schneier, S., 2000. Lies: Digital Security in a Networked World Vol. 21, 318–333.
Sommestad, T., Ekstedt, M., Holm, H., 2013. The cyber security modeling language: a
tool for assessing the vulnerability of enterprise system architectures. IEEE Syst.
J. 7 (3), 363–373.
Stappers, F.P.M., Weber, S., Reniers, M.A., Andova, S., Nagy, I., 2012. Formalizing a
domain speciﬁc language using SOS: an industrial case study. In: Sloane, A.,
Aßmann, U. (Eds.), Software Language Engineering. Springer Berlin Heidelberg,
Berlin, Heidelberg, pp. 223–242.
Szlenk, M., 2006. Formal semantics and reasoning about UML class diagram. In:
Proceedings of the International Conference on Dependability of Computer Sys-
tems, pp. 51–59. doi:10.1109/DEPCOS-RELCOMEX.2006.27.
Vigo, R., Nielson, F., Nielson, H.R., 2014. Automated generation of attack trees. In:
IEEE 27th Computer Security Foundations Symposium, CSF 2014, pp. 337–350.
Vienna, Austria, 19–22 July, 2014
Wang, L., Jajodia, S., Singhal, A., Cheng, P., Noel, S., 2014. k-Zero day safety: a net-
work security metric for measuring the risk of unknown vulnerabilities. IEEE
Trans Dependable Secure Comput 11 (1), 30–44. doi:10.1109/TDSC.2013.24.
Weiss, J.D., 1991. A system security engineering process. In: 14th Annual NCSC/NIST
National Computer Security Conference, pp. 572–581.
Wideł, W., Audinot, M., Fila, B., Pinchinat, S., 2019. Beyond 2014: formal methods
for attack tree–based security modeling. ACM Comput. Surv. 52 (4), 75:1–75:36.
doi:10.1145/3331524.
Williams, L., Lippmann, R., Ingols, K., 2008. GARNET: A Graphical Attack Graph and
Reachability Network Evaluation Tool. Springer.
Xie, P., Li, J.H., Ou, X., Liu, P., Levy, R., 2010. Using Bayesian networks for cyber secu-
rity analysis. In: 2010 IEEE/IFIP Int. Conf. on Dependable Systems and Networks
(DSN). IEEE, pp. 211–220.
Xiong, W., Hacks, S., Lagerström, R., 2021. A method for assigning probability distri-
butions in attack simulation languages. Complex Syst. Inf. Model. Q. (26) 55–77.
Wojciech Widel received the PhD degree in mathematics from the AGH University
of Science and Technology, Kraków, Poland, in 2017, and the second PhD degree in
computer science from INSA Rennes, France, in 2019. He is working as a Statistician
at TIER Mobility, Poland. Previously, he worked as a Postdoctoral Researcher with
the Division of Network and Systems Engineering, KTH Royal Institute of Technol-
ogy, Sweden. His research was focused on analysis methods for graphical security
models and structural graph theory.
Simon Hacks is senior lecturer for information systems at Department of Com-
puter and Systems Sciences, Stockholm University, Sweden. His research interests
lie in the quality of Enterprise Architecture (EA) and its models. Therefore, he has
coined the term of EA Debt as an extension of Technical Debt, which provides a
holistic view on organizations beyond technical aspects. Moreover, he performs re-
search on the reuse of different models for attack simulations. In line, he facilitates
the Meta Attack Language (MAL) that allows to provide domain speciﬁc languages
(DSL) tailored to the needs of different stakeholders. Finally, he aims to provide
tooling around MAL to ensure the quality of the created MAL DSLs. He received his
PhD from RWTH Aachen University, Germany in the ﬁeld of EA modeling.
Pontus Johnson is a professor at the Royal Institute of Technology (KTH) in Stock-
holm, Sweden. His research interests mainly lie in the area of cyber security and
the analysis of architectural models of computer networks - in particular simulat-
ing cyber attacks on such networks. Pontus supervises a number of PhD students
and holds courses on Ethical Hacking. He is, since 2020, the director of the Center
for Cyber Defense and Information Security at KTH. He received his MSc from the
Lund Institute of Technology in 1997 and his PhD and Docent titles from the Royal
Institute of Technology in 2002 and 2007. He was appointed professor in 2009.
Mathias Ekstedt received the MSc, PhD, and Docent degrees from KTH Royal Insti-
tute of Technology, in 1999, 2004, and 2010, respectively. He has been a Professor
in industrial information and control systems with the KTH Royal Institute of Tech-
nology since 2015. Much of his research interest includes developing formalisms
for analyzing security vulnerabilities of system architectures through the means of
probabilistic attack/defense graphs. He is the founder and director of KTH’s Master
program in cybersecurity.
Robert Lagerström is a professor at the School of Electrical Engineering and Com-
puter Science, KTH Royal Institute of Technology, Sweden. His research is focused
on enterprise security, threat modeling, attack simulations, vehicle security, and vi-
able cities. Robert is a member of the Young Academy of Sweden and one of the
founders of foreseeti.
12
