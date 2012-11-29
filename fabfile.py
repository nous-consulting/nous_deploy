from nous_deploy import services
from nous_deploy import ubuntu
from nous_deploy import vututi
from nous_deploy import jenkins
from nous_deploy import psql
from nous_deploy import sentry

ignas = ('ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAIEA1k5A4ViR29O3XEride/ZIO52LNwEPVyTh'
         'v8Rk9pweyMrlPoyg43TG+slndvy4Vju73tnd1fGWDrmAast9WVLm5Pd5GaWCtP4WU8I24'
         'nsohf7Gz0bo84SMp7ROFAmcnPuq2j5/39KZzbDW810fVCpxD5+qsDTusTcCA4yrROxjUU'
         '= ignas@pow.lt')
frgtn = ('ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAgByG8k8a7n2mTWPr9q19KgzZArLBlinp0EXc'
         'uQApWl0xB12i6zGU8x9vuKtLwInXWFDVOS5H2GvTPAfd0KXIXT82QsLMcpe7ihwClXE1X'
         'sAwKY5x3VFvMNuTuvLDE3NUCt6RgHdW/nTOuINUrS4iiSUe+zR/olQfBBip+4UnfFXdGa'
         'H4d+bDMUSp7ivdEntx3bpbxgzVFSKz9KkBesyoFXz38J3Vfn980TlLSllfzlF1c9jF+Iw'
         'PjzVJVegeSTLBBGGFoJw7PZnoOSu8I+OtuSyW/Z90wU+hFnLdaUswhtmC5JlWZYH037ME'
         'DTzNziQOrETlB09hwduU46noR/z+TgaKioXcIPNE3gZs+FcIZhryc1abMcEeUvEzCl+ZS'
         '64sQLPsRQ4N8+5suSGim2TAZs8XvQWqewB5PPuJ8LpyXiWlcSh+DFb7DLUQyF97HH9Dm+'
         'BUKbUeTg2nljh02Vt7TCWsaxnxvukWpzrxfNIuOfu6r/LMsiF7rgUwwgVuqCzM7QuY3gb'
         'I/HLN9BpUaHxwaWJ1L44Wyni0GAisGDVdOZeNL6FD4QovoOwZMJujajEoeUXh2JDkw4mq'
         'HgQ3XpB9zMwMK4uTmgxEgYgLr338vPhbwOZ2kV9wrpvWsvtpt+Trkuz/lKomdry7BdP5E'
         'D6Od58Wsw4WZ4qFCp1HOrQf0ZMSw== frgtn@thkp')


servers = [ubuntu.Server(host='sentry.frgtn.net',
                         name='vututi',
                         settings={'identities': [('', ignas), ('', frgtn)]},
                         services=[psql.Postgresql(name='ututi_db',
                                                   user='ututi',
                                                   settings={'port': 57861,
                                                             'password': 'duarkliukaivarshkepienas',
                                                             'version': '8.4'}),
                                   # sentry.Sentry(name='sentry'),
                                   vututi.VUtuti(name='ututi',
                                                 user='ututi',
                                                 settings={'db': 'ututi_db',
                                                           'port': 57862,
                                                           'host_name': 'vututi.frgtn.net'}),
                                   jenkins.Jenkins(name='jenkins',
                                                   user='jenkins'),
                                   sentry.Sentry(name='sentry2',
                                                 user='sentry2',
                                                 settings={'hostname': 'sentry.frgtn.net',
                                                           'port': 19001,
                                                           'admin_username': 'admin',
                                                           'admin_email': 'saulius@nous.lt',
                                                           'admin_password': 'medausstatinaite'})
                                   # services.Git(name='git')
                                   ]),
           # services.Server(host='ututi.com',
           #                 name='ututi',
           #                 services=[services.Ututi(name='ututi')]
           #                 ),
           # services.Server(host='beta.busyflow.com',
           #                 name='beta_busyflow_com',
           #                 services=[services.BusyFlow(name='busyflow')]
           #                 ),
           # services.Server(host='celery.busyflow.com',
           #                 name='celery_busyflow_com',
           #                 services=[services.BusyFlowCeleryWorker(name='celery')]
           #                 ),
           ]


globals().update(services.init(servers))
