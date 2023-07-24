from nsukit.tools.logging import logging
simulation_ctl = False
try:
    if simulation_ctl:
        from .xdma_sim import Xdma
    else:
        from .xdma import Xdma
except OSError as e:
    logging.warning(msg=e)
    from .xdma_sim import Xdma
