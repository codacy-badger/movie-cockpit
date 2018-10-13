SUMMARY = "MoviePlayer Extentions"
MAINTAINER = "dream-alpha"
SECTION = "extra"
PRIORITY = "optional"
RDEPENDS_${PN} = "python-json python-html python-requests"

require conf/license/license-gplv3.inc

inherit gitpkgv pythonnative gettext
SRCREV = "${AUTOREV}"
PV = "4.0.+git${SRCPV}"
PKGV = "4.0.+git${GITPKGV}"

SRC_URI="git://github.com/dream-alpha/MovieCockpit.git"

S = "${WORKDIR}/git"

PACKAGES =+ "${PN}-src"
PACKAGES =+ "${PN}-po"
FILES_${PN} = "/etc /usr/lib"
FILES_${PN}-src = "\
	/usr/lib/enigma2/python/Components/Converter/*.py \
	/usr/lib/enigma2/python/Components/Renderer/*.py \
	/usr/lib/enigma2/python/Components/Sources/*.py \
	/usr/lib/enigma2/python/Plugins/Extensions/MovieCockpit/*.py \
	"
FILES_${PN}-po = "/usr/lib/enigma2/python/Plugins/MovieCockpit/locale/*/*/*.po"

inherit autotools-brokensep

EXTRA_OECONF = "\
    BUILD_SYS=${BUILD_SYS} \
    HOST_SYS=${HOST_SYS} \
    STAGING_INCDIR=${STAGING_INCDIR} \
    STAGING_LIBDIR=${STAGING_LIBDIR} \
"

CONFFILES_${PN} = ""

do_populate_sysroot[noexec] = "1"
do_package_qa[noexec] = "1"

pkg_postinst_${PN}() {
#!/bin/sh
echo ""
echo "***********************************"
echo "*          MovieCockpit           *"
echo "*               by                *"
echo "*          dream-alpha            *"
echo "***********************************"
echo ""
echo "Plugin MovieCockpit installed successfully."
echo "Please restart DreamOS now!"
echo ""
exit 0
}

pkg_postrm_${PN}() {
#!/bin/sh
rm -rf /usr/lib/enigma2/python/Plugins/Extensions/MovieCockpit
rm /usr/lib/enigma2/python/Components/Converter/MVC*
rm /usr/lib/enigma2/python/Components/Renderer/MVC*
rm /usr/lib/enigma2/python/Components/Sources/MVC*
rm -rf /usr/share/enigma2/MovieCockpit
rm /etc/enigma2/moviecockpit.db
echo ""
echo "Plugin MovieCockpit removed."
echo "Please restart DreamOS now!"
exit 0
}
