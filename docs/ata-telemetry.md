# ATA protocol diagnostics

This change consumes the additive `ParsedDeviceState.ata_telemetry` API proposed
for pymitsubishi. The existing `pymitsubishi==0.6.1` requirement is intentionally
unchanged until that API is released: with an older dependency, existing
entities still work and no new telemetry entities are created. The maintainer
must bump the requirement to the released API version before enabling this
feature in a release. No unpublished version number is assumed.

The sensor platforms add diagnostic entities for reported status bits, actual
fan speed code, compressor frequency, remote locks and raw/candidate codes.
All new diagnostics are disabled by default. Enable the desired entities from
the device page. No existing entity ID or interpretation is changed.

The protocol overview exposes decoded values, packet quality, candidate field
names and unknown bytes. Full raw frames are available in the device's Download
diagnostics result rather than duplicated in every entity's Recorder attributes.
Configuration, IP addresses, MAC addresses, serial numbers and response XML are
excluded. Unknown framed data still needs review before public sharing.

Missing/invalid/conflicting packets are unavailable, never a false defrost flag.
Transport failure makes all telemetry entities unavailable. The coordinator's
existing refresh drives every entity, with no new polling or control requests.

Interpretation follows the [community protocol reference](https://muart-group.github.io/developer/it-protocol).
Documented does not guarantee model support; a constant zero may be unsupported.
Raw timer bytes have no guessed minutes unit. Error display code `A0` means all
clear. Candidate auto-leader, secondary temperature and capability interpretations
are explicitly labeled through metadata. Secondary temperature is not established
as discharge-air or coil temperature. The feature does not measure heat or COP.

On multisplits, correlate both indoor reports as one outdoor machine, validate
against observed defrosts and retain freshness checks before considering control.
