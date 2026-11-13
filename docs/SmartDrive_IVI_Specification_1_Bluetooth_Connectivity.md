# SmartDrive IVI -- Bluetooth Connectivity and Phone Pairing

## Software Requirements Specification (SRS)

**Document version:** 1.1\
**Status:** Workshop baseline (1.1: CAPL supplementary test scripts added)\
**System:** SmartDrive In-Vehicle Infotainment (IVI) Simulator\
**Module:** Bluetooth Connectivity and Phone Pairing\
**Intended audience:** QA engineers, test analysts, automation engineers
and developers

------------------------------------------------------------------------

## 1. Purpose

This specification defines the functional and quality requirements for
the Bluetooth connectivity and phone-pairing module of a simulated
automotive infotainment system.

It is intended for a two-day QA workshop using GitHub Copilot.
Participants will analyse requirements, identify ambiguities, design
tests, generate test data, implement automated checks, execute tests and
report defects.

This is a **software-only training simulator**. It does not control real
vehicle systems and is not intended for production automotive use.

## 2. Scope

The module allows a user to:

-   Discover nearby Bluetooth devices.
-   Pair a smartphone with the infotainment system.
-   View and manage paired devices.
-   Connect and disconnect a paired device.
-   Reconnect to the last connected device under defined conditions.
-   Handle pairing failures and connection interruptions.
-   Simulate the effect of an incoming phone call on media playback.

### 2.1 In scope

-   Simulated Bluetooth device discovery.
-   Pairing and passkey verification.
-   Paired-device capacity management.
-   Active-device connection management.
-   Manual disconnect and device removal.
-   Automatic reconnection behaviour.
-   Pairing and connection error handling.
-   Simulated incoming-call interruption event.
-   CAPL test scripts (Vector CANoe) as a supplement to the primary
    Python/Pytest test suite, exercising the simulator only.

### 2.2 Out of scope

-   Real Bluetooth radio, Bluetooth stack or hardware integration.
-   Actual mobile-phone calls, contacts or call history.
-   Emergency-call functionality.
-   Audio codec quality, microphone quality or speaker performance.
-   Vehicle CAN, LIN or other in-vehicle network integration, other
    than the CAPL supplementary scripts listed in section 2.1.
-   Driver-distraction or regulatory certification.
-   Production security certification.

## 3. Actors

  -----------------------------------------------------------------------
  Actor                               Description
  ----------------------------------- -----------------------------------
  Driver / User                       Operates the infotainment
                                      interface.

  Smartphone (simulated)              Represents a Bluetooth-capable
                                      mobile device.

  IVI System                          Discovers, pairs and manages
                                      Bluetooth devices.

  QA Tester                           Validates expected behaviour and
                                      reports defects.
  -----------------------------------------------------------------------

## 4. Assumptions and constraints

1.  The simulator provides a controllable list of discoverable Bluetooth
    devices.
2.  Each simulated device has a unique device identifier, display name
    and pairing passkey.
3.  The simulator can generate connection success, failure, timeout and
    disconnection events.
4.  The maximum number of stored paired devices is five.
5.  Only one smartphone may be actively connected at a time.
6.  Bluetooth can be enabled or disabled through the simulator.
7.  Timeouts are configurable in the test environment. Unless otherwise
    stated, the default pairing timeout is 30 seconds.
8.  The system clock and device availability can be controlled during
    automated tests.

## 5. Functional requirements

### FR-BT-001: Discover available devices

The system shall allow the user to initiate a scan for nearby Bluetooth
devices.

**Acceptance criteria** - When Bluetooth is enabled and a scan is
started, the system displays the available discoverable devices returned
by the simulator. - Each result displays a device name and a
distinguishable device identifier. - The system shall not display
duplicate entries for the same device identifier in a single scan
result. - If no devices are found, the system displays an appropriate
no-devices-found message. - If Bluetooth is disabled, the system shall
prevent scanning and explain that Bluetooth must be enabled.

### FR-BT-002: Pair using passkey verification

The system shall allow the user to pair a discovered device using
passkey verification.

**Acceptance criteria** - The user can select a discovered device and
initiate pairing. - The system displays the passkey verification step. -
Pairing succeeds when the entered passkey matches the simulated device
passkey and the device accepts the request. - Pairing fails when the
passkey is incorrect or the device rejects the request. - A failed
pairing attempt shall display an appropriate error message. - A
successfully paired device is added to the paired-device list.

### FR-BT-003: Support a maximum of five paired devices

The system shall store a maximum of five paired devices.

**Acceptance criteria** - The system permits pairing while fewer than
five devices are stored. - When five devices are already stored, the
system shall not add a sixth device. - The system shall display a
message explaining that the paired-device limit has been reached. - The
user can remove an existing paired device and then pair another device.

### FR-BT-004: Allow only one active smartphone connection

The system shall allow only one smartphone to be actively connected at a
time.

**Acceptance criteria** - A paired device can be connected when no other
smartphone is actively connected. - When the user requests connection to
another paired device while one is active, the system shall not maintain
two active smartphone connections. - The system shall communicate the
outcome of the connection request to the user. - The active connection
status shall be accurately reflected in the device list.

**Workshop clarification point:** The baseline does not define whether
connecting a second device should automatically disconnect the first
device or require the user to disconnect it first. Participants should
identify this as an ambiguity and propose a decision.

### FR-BT-005: Automatically reconnect to the last connected device

The system shall attempt to reconnect to the last connected paired
device when Bluetooth is enabled and that device is available.

**Acceptance criteria** - The system records which paired device was
last connected. - When Bluetooth is enabled, the system attempts
reconnection if the last connected device is available. - The system
displays the reconnection status. - If the device is unavailable, the
system remains in a disconnected state and displays an appropriate
status. - The system shall not attempt to connect to a device that has
been removed from the paired-device list.

**Workshop clarification point:** The baseline does not define the
number of retries, retry interval or maximum reconnection duration.
These should be raised during requirement review.

### FR-BT-006: Disconnect and remove a paired device

The system shall allow the user to disconnect an active device and
remove a paired device.

**Acceptance criteria** - The user can disconnect the currently
connected device. - After disconnection, the device remains in the
paired-device list. - The user can remove a paired device from the
list. - A removed device is no longer treated as paired. - The user
receives confirmation or status feedback after the operation. - Removing
the active device shall result in that device becoming disconnected.

### FR-BT-007: Handle pairing failures and timeouts

The system shall provide appropriate feedback when pairing fails or
times out.

**Acceptance criteria** - An incorrect passkey results in a
pairing-failed status. - A device rejection results in a pairing-failed
status. - If pairing is not completed within the configured 30-second
timeout, the pairing attempt is cancelled. - The user is informed when
the pairing attempt times out. - A failed or timed-out attempt shall not
add the device to the paired-device list. - The user can initiate a new
pairing attempt after a failure.

### FR-BT-008: Handle incoming calls during media playback

The system shall temporarily interrupt media playback when an
incoming-call event is received from the currently connected smartphone.

**Acceptance criteria** - When an incoming-call event is received during
media playback, the system pauses or ducks media audio according to the
configured interruption mode. - The system displays an incoming-call
indication. - When the simulated call ends, the system applies the
configured media-resumption behaviour. - If the Bluetooth connection is
lost during the call, the system updates the connection status. - The
system shall not resume playback if the configured policy or user
setting prevents automatic resumption.

**Workshop clarification point:** The baseline allows either pause or
audio ducking, but the selected behaviour must be configured and
testable. The exact post-call resumption policy must also be made
explicit before final test execution.

## 6. Non-functional requirements

### NFR-BT-001: Response time

For the simulator, the UI shall provide visible feedback for a user
action within two seconds, excluding simulated external-device response
time.

### NFR-BT-002: Usability

The system shall display clear status messages for scanning, pairing,
connecting, disconnecting and failure conditions.

### NFR-BT-003: Reliability

A failed scan, pairing attempt or connection attempt shall not corrupt
the existing paired-device list.

### NFR-BT-004: State consistency

The displayed device state shall be consistent with the simulator's
underlying state after each completed operation.

### NFR-BT-005: Testability

The simulator shall provide controllable test hooks or fixtures to set
device availability, passkey validity, operation delays and connection
outcomes.

### 6.1 CAPL documentation requirements

Supplements NFR-BT-005. Public sources: Vector CANoe online help
(help.vector.com), Vector Knowledge Base (kb.vector.com), vector.com
application notes, and the offline CAPL function reference installed
with CANoe.

  ------------------------------------------------------------------------
  ID              Requirement                                 Trace
  --------------- ------------------------------------------- ------------
  DOC-CAPL-001    Each CAPL test script shall cite the        NFR-BT-005
                  Vector help or Knowledge Base entry for
                  every CAPL built-in function it uses
                  (functions that are not standard C-style
                  constructs).

  DOC-CAPL-002    Each citation shall record the CANoe        NFR-BT-005
                  version (for example, `CANoe 17 SP3`) in
                  the script header, because function
                  availability varies by version.

  DOC-CAPL-003    Forums and blogs shall not be the sole      NFR-BT-005
                  reference for any CAPL function.
  ------------------------------------------------------------------------

CAPL tests that depend on the unresolved items OQ-01 to OQ-08 shall be
marked blocked and raised as clarification questions.

## 7. Core device states

The following states are expected to be represented by the simulator:

  State            Meaning
  ---------------- -----------------------------------------------------
  Not discovered   Device has not been found in the current scan.
  Discovered       Device is visible and available for pairing.
  Pairing          Pairing is in progress.
  Paired           Device is stored but not connected.
  Connecting       A connection attempt is in progress.
  Connected        Device is the active smartphone connection.
  Disconnected     Previously connected device is no longer connected.
  Pairing failed   Pairing attempt failed or timed out.

### 7.1 Example state transitions

-   Discovered → Pairing → Paired
-   Discovered → Pairing → Pairing failed
-   Paired → Connecting → Connected
-   Paired → Connecting → Disconnected
-   Connected → Disconnected
-   Connected → Removed
-   Paired → Removed

QA participants should review whether these states and transitions are
complete, mutually clear and testable.

## 8. Key use cases

### UC-BT-001: Pair a smartphone

**Preconditions** - Bluetooth is enabled. - The smartphone is
discoverable. - Fewer than five devices are currently paired.

**Main flow** 1. User starts device discovery. 2. System displays
available devices. 3. User selects a smartphone. 4. System initiates
pairing. 5. System requests passkey verification. 6. User enters the
correct passkey. 7. Smartphone accepts the pairing request. 8. System
adds the smartphone to the paired-device list. 9. System displays
successful pairing status.

**Alternative flows** - Incorrect passkey: pairing fails and an error is
displayed. - Device rejects pairing: pairing fails and an error is
displayed. - Timeout: pairing is cancelled after 30 seconds. - Capacity
reached: pairing is blocked and the user is informed.

### UC-BT-002: Connect a paired smartphone

**Preconditions** - The smartphone is already paired. - Bluetooth is
enabled. - No other smartphone is actively connected.

**Main flow** 1. User opens the paired-device list. 2. User selects a
paired smartphone. 3. User requests connection. 4. System initiates the
connection. 5. Smartphone accepts the connection. 6. System marks the
smartphone as connected.

**Alternative flows** - Device unavailable: system reports that
connection could not be established. - Another smartphone is active:
system applies the defined single-active-connection policy. - Bluetooth
disabled: system prevents the connection attempt and informs the user.

## 9. Test design guidance for the workshop

Participants should derive test conditions and test cases using the
following ISTQB CTFL techniques.

  -----------------------------------------------------------------------
  Technique                           Suggested application
  ----------------------------------- -----------------------------------
  Equivalence Partitioning            Correct passkey, incorrect passkey,
                                      unavailable device.

  Boundary Value Analysis             Paired-device counts of 4, 5 and 6;
                                      pairing timeout around 30 seconds.

  Decision Table Testing              Pairing outcome based on Bluetooth
                                      status, device availability,
                                      passkey validity and device
                                      capacity.

  State Transition Testing            Pairing, connecting, connected,
                                      disconnected and removed states.

  Use Case Testing                    Complete smartphone pairing and
                                      connection workflows.

  Error Guessing                      Repeated pairing, device
                                      disappearance during pairing,
                                      restart during reconnection.

  Exploratory Testing                 Rapid user actions and unexpected
                                      event combinations.
  -----------------------------------------------------------------------

### 9.1 Minimum suggested test coverage

The following are workshop targets, not formal product acceptance
thresholds:

-   Positive and negative pairing scenarios.
-   Device-capacity boundary scenarios.
-   Single-active-connection scenarios.
-   Automatic reconnection scenarios.
-   Pairing timeout and failure scenarios.
-   Disconnect and remove scenarios.
-   Incoming-call interruption scenarios.
-   Regression tests for previously working behaviour.

## 10. Deliberate requirement-review challenges

These points are intentionally unresolved. QA participants should
identify them during requirement analysis rather than silently assume
behaviour.

  -----------------------------------------------------------------------
  ID                      Open question /         Expected QA activity
                          ambiguity               
  ----------------------- ----------------------- -----------------------
  OQ-01                   What should happen when Raise clarification and
                          a second smartphone is  define expected
                          connected while another behaviour.
                          is active?              

  OQ-02                   How many automatic      Identify missing retry
                          reconnection attempts   policy and propose
                          are allowed?            testable values.

  OQ-03                   What is the retry       Request measurable
                          interval and total      timing requirements.
                          reconnection window?    

  OQ-04                   Does the five-device    Clarify storage and
                          limit include           capacity rules.
                          unavailable or          
                          previously paired       
                          devices?                

  OQ-05                   What should happen if   Define expected state
                          the device disappears   and error handling.
                          during passkey          
                          verification?           

  OQ-06                   Should media resume     Clarify configurable
                          automatically after     policy and acceptance
                          every call?             criteria.

  OQ-07                   What happens if         Define interruption and
                          Bluetooth is disabled   recovery behaviour.
                          during an active call?  

  OQ-08                   Can a user cancel a     Confirm cancellation
                          pairing operation       behaviour and expected
                          before the timeout?     state.
  -----------------------------------------------------------------------

**Instruction for workshop facilitators:** Do not provide all answers
immediately. Ask participants to identify ambiguity, assess testability
and propose precise acceptance criteria. Record agreed decisions as
requirement changes.

## 11. Suggested GitHub repository structure

``` text
smartdrive-ivi/
├── README.md
├── docs/
│   ├── SRS-Bluetooth-Connectivity.md
│   ├── test-strategy.md
│   ├── test-scenarios.md
│   └── test-summary.md
├── src/
│   └── bluetooth/
├── tests/
│   ├── unit/
│   ├── api/
│   └── ui/
├── test-data/
│   └── bluetooth-devices.json
├── defects/
└── .github/
    └── copilot-instructions.md
```

## 12. Suggested GitHub Copilot activities

1.  Review the SRS and identify ambiguous, inconsistent, missing and
    untestable requirements.
2.  Generate clarification questions for the open questions in Section
    10.
3.  Derive test conditions and test scenarios for every functional
    requirement.
4.  Generate test cases using equivalence partitioning, boundary value
    analysis, decision tables and state transition testing.
5.  Generate positive, negative and boundary test data.
6.  Implement a simple Bluetooth simulator or mock service.
7.  Generate automated tests using Pytest and, if a web UI is
    implemented, Playwright.
8.  Execute tests and use Copilot to analyse failures.
9.  Create defect reports with reproducible steps, expected results and
    actual results.
10. Review test coverage and generate a test execution summary.

## 13. Definition of workshop completion

The workshop implementation is considered complete when participants
have:

-   Reviewed the requirements and documented clarification questions.
-   Produced traceable test scenarios and test cases.
-   Implemented a basic simulator or testable mock.
-   Automated a representative set of positive, negative and boundary
    tests.
-   Executed the tests and analysed at least one seeded failure.
-   Produced a defect report and a concise test summary.

## 14. Requirement review decisions

Decisions below come from the requirement-review questionnaire. They are
default recommendations pending owner confirmation. OQ-01..OQ-08 are not
decided here and remain open (Section 10): Q-07, Q-08, Q-10, Q-14, Q-15,
Q-25, Q-28 and Q-29.

| Q-ID | Req | Decision |
|------|-----|----------|
| Q-01 | FR-BT-001 | Scan ends when the simulator returns its list; 'no devices found' if the list is empty. |
| Q-02 | FR-BT-001 | Already-paired devices are hidden from scan results. |
| Q-03 | FR-BT-002 | Passkey is a 6-digit numeric value shown on the simulated device. |
| Q-04 | FR-BT-002 | A wrong passkey ends the attempt immediately as pairing failed. |
| Q-05 | FR-BT-002 | Pairing a device already in the paired list is blocked with an 'already paired' message. |
| Q-06 | FR-BT-002 | A second pairing request is rejected while one attempt is in progress. |
| Q-09 | FR-BT-003 | Capacity is checked at device selection, before the passkey step. |
| Q-11 | FR-BT-004 | Target already Connected: no change, status shown. Another device Connecting: request rejected until it finishes. |
| Q-12 | FR-BT-004 | Connection timeout is 30 s; the device returns to Paired. |
| Q-13 | FR-BT-004 | The simulator contains smartphones only. |
| Q-16 | FR-BT-005 | A manual disconnect clears the last connected device; no automatic reconnection. |
| Q-17 | FR-BT-005 | A manual connection during reconnection stops the reconnection. |
| Q-18 | FR-BT-003, FR-BT-005 | Paired list and last connected device persist across restart; reconnection restarts after restart. |
| Q-19 | FR-BT-005 | After the last connected device is removed, there is no last connected device and no reconnection. |
| Q-20 | FR-BT-006 | Status message after removal; no confirmation prompt. |
| Q-21 | FR-BT-006 | No connected device: status message. Connecting device: attempt cancelled, device returns to Paired. |
| Q-22 | FR-BT-007 | Timeout counts from when the passkey step is shown; passkey accepted up to and including 30.0 s. |
| Q-23 | FR-BT-007 | Timeout shows a distinct message; state is 'Pairing failed'. |
| Q-24 | FR-BT-007 | No limit and no waiting time after failed attempts. |
| Q-26 | FR-BT-008 | Interruption mode is a setting with values 'pause' and 'duck'; default 'pause'. |
| Q-27 | FR-BT-008 | Ducking sets audio to 30 percent of current volume; original volume is restored. |
| Q-30 | FR-BT-008, NFR-BT-005 | Incoming, answered-then-ended, rejected and missed events all end the interruption. |
| Q-31 | FR-BT-008 | Incoming-call event from a non-connected paired device is ignored. |
| Q-32 | FR-BT-008 | Incoming-call indication is always shown, with or without media playing. |
| Q-33 | FR-BT-008 | Connection loss during a call: status 'Disconnected', indication cleared, media follows the resumption policy of the setting in OQ-06 (open). |
| Q-34 | NFR-BT-001 | Visible feedback = any change in the status area; measured from input event to status change; applies to FR-BT-001 to FR-BT-008. |
| Q-35 | NFR-BT-001 | The 2 s limit applies even while the simulated device delay is running. |
| Q-36 | NFR-BT-002 | Messages must name the condition; exact wording is free. |
| Q-37 | NFR-BT-002 | Status messages cover all operations in FR-BT-001 to FR-BT-008. |
| Q-38 | NFR-BT-003 | 'Not corrupt' means the same entries, order, names, identifiers and last connected device before and after a failed operation. |
| Q-39 | NFR-BT-004 | All states in Section 7 are compared; an operation completes at Paired, Connected, Disconnected, Pairing failed or Removed. |
| Q-40 | NFR-BT-005 | A Python API provides all listed hooks plus Bluetooth on/off, incoming-call events, interruption mode, restart and system clock. |
| Q-41 | Cross-cutting | The simulator is API-only; 'UI' refers to the API status output. |
| Q-42 | FR-BT-006, Section 7 | 'Removed' is added to the state table; it means not in the paired list. |
| Q-43 | FR-BT-004, FR-BT-006, Section 7 | 'Disconnected' applies only to previously connected devices; a failed first connection returns to Paired. |
| Q-44 | Section 7.1 | The seven missing transitions (Pairing to Cancelled, Pairing to Pairing failed on timeout, Connecting to Pairing failed, Disconnected to Connecting, Disconnected to Removed, Pairing failed to Discovered, Discovered to Not discovered) are adopted as written. The full table is still pending. |
| Q-45 | FR-BT-005 | Automatic reconnection uses the Connecting state with status text 'Reconnecting'. |
| Q-46 | FR-BT-004, UC-BT-002 | 'Another smartphone active' is an alternative flow; it is removed from the preconditions. |
| Q-47 | FR-BT-001, FR-BT-002, FR-BT-004, FR-BT-005 | Turning Bluetooth off cancels scan, pairing and connecting with no change to the paired list; a connected device becomes Disconnected. |
| Q-48 | NFR-BT-005, DOC-CAPL-001 | CAPL scripts reach the simulator through CANoe system variables mapped to the simulator hooks. |
| Q-49 | DOC-CAPL-001 | Every function in the CANoe CAPL function reference is cited, excluding C keywords and operators. |
| Q-50 | DOC-CAPL-002 | The CANoe version is recorded once in the script header; baseline is CANoe 17 SP3. |
| Q-51 | DOC-CAPL-003 | Acceptable sources are the four named in Section 6.1; forums and blogs are not a sole reference. |

------------------------------------------------------------------------

**End of specification**

*This is a synthetic workshop specification. It is not an OEM
specification, an ISO 26262 safety case, a Bluetooth qualification
document or a production-ready automotive system requirement.*
