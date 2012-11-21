from nous_deploy import services

servers = [services.Server(host='sentry.frgtn.net',
                           name='sentry_frgtn_net',
                           services=[services.Sentry(name='sentry'),
                                     services.Sentry(name='sentry2')]
                           ),
           services.Server(host='sentry.frgtn.net',
                           name='vututi',
                           services=[services.Sentry(name='sentry'),
                                     services.Ututi(name='ututi'),
                                     services.Jenkins(name='jenkins'),
                                     services.Git(name='git')]),
           services.Server(host='ututi.com',
                           name='ututi',
                           services=[services.Ututi(name='ututi')]
                           ),
           services.Server(host='beta.busyflow.com',
                           name='beta_busyflow_com',
                           services=[services.BusyFlow(name='busyflow')]
                           ),
           services.Server(host='celery.busyflow.com',
                           name='celery_busyflow_com',
                           services=[services.BusyFlowCeleryWorker(name='celery')]
                           ),
           ]


globals().update(services.init(servers))
