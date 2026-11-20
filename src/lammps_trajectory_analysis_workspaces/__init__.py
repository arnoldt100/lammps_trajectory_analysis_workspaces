#! /usr/bin/env python3


def import_mdanalysis_with_affinity(env_var="MDA_RESTORE_AFFINITY"):
    """Import MDAnalysis while optionally preserving the original CPU affinity mask."""
    import os

    restore = os.environ.get(env_var, "").lower() in ("1", "true", "yes")
    can_manage_affinity = hasattr(os, "sched_getaffinity") and hasattr(os, "sched_setaffinity")

    orig_affinity = None
    if restore and can_manage_affinity:
        orig_affinity = os.sched_getaffinity(0)

    import MDAnalysis

    if orig_affinity is not None:
        os.sched_setaffinity(0, orig_affinity)

    return MDAnalysis


MDAnalysis = import_mdanalysis_with_affinity()


__all__ = ["MDAnalysis",
           "import_mdanalysis_with_affinity"]
