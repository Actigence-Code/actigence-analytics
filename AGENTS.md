
<!-- ACTIGENCE:mandatory-core:start -->
Core is mandatory in every Actigence-Code project, clone and machine. Core contains only Theme (including UI), Assistance and i18n. Follow core-consumer.json and the mandatory workflow, pinned to immutable Core governance a5a0c1929f81d7eaae6f4f3939075f2e916e6919. All maintained UI uses exact published Theme/UI archives and the common locale controller/cookie actigence_language. Preserve real catalogues, unsupported shared choices and native permissions/data. A historical boundary is not migrated and cannot release UI changes until adapted. Backend/hosted boundaries remain explicit. Independent Theme/UI repositories are retired.
Canonical contract: https://github.com/Actigence-Code/actigence-core/blob/a5a0c1929f81d7eaae6f4f3939075f2e916e6919/docs/CORE-MANDATORY.md
<!-- ACTIGENCE:mandatory-core:end -->

<!-- ACTIGENCE:mandatory-mail:start -->
## Actigence Mail : obligation absolue du propriétaire, 2026-10-22

Aucun courriel des applications Actigence ni des serveurs ne part autrement que via Actigence Mail. Source amont unique : `/etc/actigence/mail/smtp2go.env` sur OVH, relue à chaque remise, sans copie de configuration, secret dans Git, ancien identifiant ni transport de repli. Toutes les notifications, files d'attente, tâches planifiées, scripts, alertes système et serveurs SMTP de workspace sont concernés. Les consommateurs utilisent le relais privé Actigence Mail ; seul celui-ci accède à SMTP2GO. Source absente, illisible ou invalide : refuser, jamais contourner. Préserver permissions, destinataires, anti-doublons et protections de sandbox. Appliquer `docs/MAIL-MANDATORY.md`, `mail-consumer.json` et le contrôle GitHub obligatoire. Cette instruction remplace toute ancienne recommandation de fournisseur ou SMTP privé.
<!-- ACTIGENCE:mandatory-mail:end -->
