# Actigence Mail obligatoire

Instruction absolue du propriétaire du 22 octobre 2026 : **aucun courriel des
applications Actigence ou des serveurs ne part autrement que via Actigence Mail**.
Cela couvre notifications, authentification, invitations, rapports, partages,
files d'attente, tâches planifiées, sauvegardes, alertes et commandes système.

La source unique des paramètres et identifiants en amont est
`/etc/actigence/mail/smtp2go.env` sur OVH. Actigence Mail relit ce fichier à chaque remise.
Son format actuel est un export SMTP2GO de six lignes : identifiant, mot de
passe, serveur, port, ports TLS alternatifs et ports SSL. Il n'est jamais sourcé
comme un script shell. Le fichier original a été déplacé hors de `/tmp` selon la dernière instruction propriétaire ; l’ancien chemin est absent, sans lien ni copie. Il reste hors Git, archives, images,
logs et variables du navigateur. Ne pas en fabriquer une autre copie de
configuration ni conserver d'anciens identifiants comme repli.

Les consommateurs utilisent exclusivement le relais privé Actigence Mail sur
le port 25 : `127.0.0.1` sur OVH ou la passerelle privée du conteneur. Le host
de passerelle peut être fourni par `ACTIGENCE_MAIL_RELAY_HOST`, validé comme
adresse privée par l'adaptateur. Ce paramètre sélectionne l'entrée locale de
Mail, jamais un fournisseur SMTP. Depuis un NAS, utiliser le chemin SSH OVH
documenté (`sendmail -t -oi`) ou une entrée Tailscale autorisée. Aucun secret
SMTP2GO n'est distribué aux applications ou aux NAS.

Le relais fait partie d'Actigence Mail et utilise Exim pour la soumission et
la file système. Son unique transport sortant appelle le composant Mail
`deliver.py` sans shell, sous l'identité Debian-exim. Ce composant relit la source,
impose AUTH et TLS avec vérification du certificat et conserve un registre
opaque avant DATA. Une perte d'accusé de réception reste en quarantaine, sans
nouvelle soumission amont. Chaque destinataire conserve une remise indépendante
et son état ; aucune adresse ni corps n'est enregistré dans ce registre. Les
boîtes locales et alias système natifs sont conservés. Fichier absent, illisible ou invalide :
refus temporaire de la soumission ou de la remise ; aucune autre route. Une
indisponibilité ne doit jamais être présentée comme un succès de livraison.
L'acceptation par le relais ne prouve ni l'acceptation amont ni la réception.

Les transports SMTP directs, API de fournisseurs de courriels, comptes SMTP
de workspace, failovers externes et MX directs sont interdits. Le MTA système
(`mail`, `sendmail`, cron) utilise le même relais et la même source. Le pare-feu
IPv4/IPv6 interdit les ports SMTP externes aux autres utilisateurs/processus
et aux conteneurs. Il conserve les tables réseau natives. Le filtrage de ports
complète la revue du code et la suppression des fournisseurs HTTP ; il ne
prétend pas analyser tout protocole arbitraire encapsulé dans HTTPS.

Conserver les contrôles d'accès, expéditeurs, destinataires, protections de
sandbox, enveloppes métier, anti-doublons et files natives. Une source SMTP
commune n'autorise aucun envoi de test à des tiers ni rejeu de l'historique.
Conserver les obligations CCI et les restrictions de sandbox déjà applicables.

Chaque dépôt déclare sa frontière dans `mail-consumer.json`. Le contrôle
`.github/workflows/actigence-mail.yml` refuse les nouveaux points d'envoi non
revus, une modification d'un adaptateur approuvé et la présence du fichier
secret dans Git. Revoir réellement un changement avant de mettre à jour son
empreinte. Les projets sans envoi restent explicitement sans envoi ; le contrat
ne crée aucune nouvelle fonctionnalité de courriel.

Implémentation du relais et exploitation :
[Actigence Mail relay](https://github.com/Actigence-Code/actigence-links/tree/main/mail-relay).
Core conserve exclusivement Theme (UI imbriqué), Assistance et i18n.
