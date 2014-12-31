if os.path.isfile('launch_tests_conf.py'):
    from launch_tests_conf import *

# Out in another dir
OUTPUT_DIR += '_bad_conditions'

# Tests both4 then with some losses or delays
NETWORK_TESTS = 'both4 both4TCL2p both4TCL5p both4TCL10p both4TCL15p both4TCL20p both4TCD5m both4TCD10m both4TCD25m both4TCD50m both4TCD100m'

# Tests with ShadowSocks
WITH_SSH_TUNNEL = False
WITH_SHADOWSOCKS = True

# Tests without MPTCP (to see the diff) and FullMesh
# (with the default path manager, we will not see the differences:
#  it will use only one IFace, the same as used without MPTCP)
WITH_TCP = True
WITH_MPTCP = False
WITH_FULLMESH = True
